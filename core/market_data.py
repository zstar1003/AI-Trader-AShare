"""
市场数据提供者
"""
import tushare as ts
from datetime import datetime, timedelta
from typing import List, Optional, Dict


class MarketDataProvider:
    """市场数据提供者"""

    def __init__(self, pro_api):
        self.pro = pro_api

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

    @staticmethod
    def get_stock_price(pro_api, ts_code: str, trade_date: str) -> Optional[Dict]:
        """获取股票某日价格"""
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
