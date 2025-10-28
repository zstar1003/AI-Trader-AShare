"""
市场数据提供者 - 支持从JSON文件读取
"""
import json
import tushare as ts
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from pathlib import Path


class MarketDataProvider:
    """市场数据提供者"""

    def __init__(self, pro_api, data_dir: Optional[Path] = None):
        self.pro = pro_api
        self.data_dir = data_dir or Path(__file__).parent.parent / "data" / "daily_prices"

    @staticmethod
    def get_trading_dates(pro_api, start_date: str, end_date: str) -> List[str]:
        """获取交易日列表"""
        try:
            df = pro_api.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
            trading_dates = df[df['is_open'] == 1]['cal_date'].tolist()
            return sorted(trading_dates)
        except Exception as e:
            print(f"获取交易日失败: {e}")
            return []

    @staticmethod
    def get_recent_trading_dates(pro_api, n_days: int = 10) -> List[str]:
        """获取最近N个交易日"""
        # 使用最近3个月的数据，确保能获取到足够的交易日
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        dates = MarketDataProvider.get_trading_dates(pro_api, start_str, end_str)

        # 返回最近的N个交易日（已排序，从旧到新）
        return dates[-n_days:] if len(dates) >= n_days else dates

    def get_stock_price_from_json(self, ts_code: str, trade_date: str) -> Optional[Dict]:
        """
        从JSON文件获取股票价格

        Args:
            ts_code: 股票代码
            trade_date: 交易日期 YYYYMMDD

        Returns:
            Dict: 价格数据
        """
        file_path = self.data_dir / f"daily_prices_{ts_code}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换日期格式 YYYYMMDD -> YYYY-MM-DD
            date_formatted = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"

            time_series = data.get("Time Series (Daily)", {})
            if date_formatted not in time_series:
                return None

            day_data = time_series[date_formatted]

            return {
                'ts_code': ts_code,
                'date': trade_date,
                'open': float(day_data['1. open']),
                'close': float(day_data['4. close']),
                'high': float(day_data['2. high']),
                'low': float(day_data['3. low']),
                'volume': float(day_data['5. volume']),
                'change': 0  # 需要计算涨跌幅
            }

        except Exception as e:
            print(f"从JSON读取失败 {ts_code} {trade_date}: {e}")
            return None

    @staticmethod
    def get_stock_price(pro_api, ts_code: str, trade_date: str) -> Optional[Dict]:
        """获取股票某日价格（从Tushare API）"""
        try:
            df = pro_api.daily(ts_code=ts_code, trade_date=trade_date)
            if df.empty:
                return None

            row = df.iloc[0]
            return {
                'ts_code': row['ts_code'],
                'date': row['trade_date'],
                'open': float(row['open']),
                'close': float(row['close']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row['vol']) if row['vol'] else 0,
                'change': float(row['pct_chg']) if row['pct_chg'] else 0
            }
        except Exception as e:
            print(f"获取股票价格失败 {ts_code} {trade_date}: {e}")
            return None

    def get_stock_price_hybrid(self, ts_code: str, trade_date: str) -> Optional[Dict]:
        """
        混合模式获取股票价格：优先从JSON读取，失败则从API获取

        Args:
            ts_code: 股票代码
            trade_date: 交易日期 YYYYMMDD

        Returns:
            Dict: 价格数据
        """
        # 先尝试从JSON读取
        data = self.get_stock_price_from_json(ts_code, trade_date)
        if data:
            return data

        # JSON没有，从API获取
        return self.get_stock_price(self.pro, ts_code, trade_date)

    def get_all_stocks_from_json(self) -> List[str]:
        """获取所有已有JSON数据的股票代码"""
        if not self.data_dir.exists():
            return []

        stock_codes = []
        for file_path in self.data_dir.glob("daily_prices_*.json"):
            filename = file_path.stem
            ts_code = filename.replace('daily_prices_', '')
            stock_codes.append(ts_code)

        return sorted(stock_codes)

    @staticmethod
    def get_stock_list(pro_api, limit: int = 50) -> List[Dict]:
        """获取股票列表（按市值排序）"""
        try:
            today = datetime.now().strftime('%Y%m%d')

            df_basic = pro_api.stock_basic(exchange='', list_status='L',
                                          fields='ts_code,symbol,name,area,industry')

            df_market = pro_api.daily_basic(trade_date=today,
                                           fields='ts_code,total_mv,turnover_rate,pe_ttm')

            if df_market.empty:
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                df_market = pro_api.daily_basic(trade_date=yesterday,
                                               fields='ts_code,total_mv,turnover_rate,pe_ttm')

            df = df_basic.merge(df_market, on='ts_code', how='inner')
            df = df.dropna(subset=['total_mv'])
            df = df.sort_values('total_mv', ascending=False).head(limit)

            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'ts_code': row['ts_code'],
                    'name': row['name'],
                    'industry': row['industry'] if row['industry'] else '未知',
                    'market_value': float(row['total_mv']) if row['total_mv'] else 0
                })

            return stocks
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []

    def get_all_stocks_with_json(self) -> List[Dict]:
        """获取所有已有JSON数据的股票（包含基本信息）"""
        stock_codes = self.get_all_stocks_from_json()

        if not stock_codes:
            return []

        try:
            # 从API获取基本信息
            df_basic = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry'
            )

            stocks = []
            for ts_code in stock_codes:
                row = df_basic[df_basic['ts_code'] == ts_code]
                if not row.empty:
                    row = row.iloc[0]
                    stocks.append({
                        'ts_code': ts_code,
                        'name': row['name'],
                        'industry': row['industry'] if row['industry'] else '未知',
                        'market_value': 0  # JSON文件中没有市值信息
                    })

            return stocks

        except Exception as e:
            print(f"获取股票基本信息失败: {e}")
            return []
