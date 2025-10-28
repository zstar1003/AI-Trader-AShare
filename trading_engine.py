"""
AI交易竞赛系统 - 核心引擎
支持多个AI模型进行模拟交易对比
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import tushare as ts
from dotenv import load_dotenv

load_dotenv()

# 配置Tushare
TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()


@dataclass
class Position:
    """持仓信息"""
    ts_code: str
    name: str
    shares: int  # 持有股数
    avg_price: float  # 平均成本
    current_price: float  # 当前价格

    @property
    def market_value(self) -> float:
        """市值"""
        return self.shares * self.current_price

    @property
    def profit_loss(self) -> float:
        """盈亏"""
        return (self.current_price - self.avg_price) * self.shares

    @property
    def profit_loss_pct(self) -> float:
        """盈亏百分比"""
        if self.avg_price == 0:
            return 0
        return ((self.current_price - self.avg_price) / self.avg_price) * 100


@dataclass
class TradeRecord:
    """交易记录"""
    date: str
    action: str  # buy/sell
    ts_code: str
    name: str
    price: float
    shares: int
    amount: float
    commission: float
    reason: str  # AI决策理由


@dataclass
class Portfolio:
    """投资组合"""
    cash: float  # 现金
    positions: Dict[str, Position]  # 持仓
    trade_history: List[TradeRecord]  # 交易历史
    daily_values: List[Dict]  # 每日资产价值

    @property
    def total_market_value(self) -> float:
        """总市值"""
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_assets(self) -> float:
        """总资产"""
        return self.cash + self.total_market_value

    @property
    def total_profit_loss(self) -> float:
        """总盈亏"""
        if not self.daily_values:
            return 0
        initial_value = self.daily_values[0]['total_assets']
        return self.total_assets - initial_value

    @property
    def total_return_pct(self) -> float:
        """总收益率"""
        if not self.daily_values:
            return 0
        initial_value = self.daily_values[0]['total_assets']
        if initial_value == 0:
            return 0
        return ((self.total_assets - initial_value) / initial_value) * 100


class TradingEngine:
    """交易引擎"""

    # 交易参数
    COMMISSION_RATE = 0.0003  # 佣金费率 0.03%
    MIN_COMMISSION = 5  # 最低佣金 5元
    STAMP_TAX_RATE = 0.001  # 印花税 0.1% (仅卖出收取)

    def __init__(self, initial_cash: float = 1000000):
        """初始化交易引擎"""
        self.initial_cash = initial_cash
        self.portfolio = Portfolio(
            cash=initial_cash,
            positions={},
            trade_history=[],
            daily_values=[]
        )

    def calculate_commission(self, amount: float, is_sell: bool = False) -> float:
        """计算交易费用"""
        commission = max(amount * self.COMMISSION_RATE, self.MIN_COMMISSION)
        if is_sell:
            # 卖出时加上印花税
            stamp_tax = amount * self.STAMP_TAX_RATE
            commission += stamp_tax
        return commission

    def buy(self, date: str, ts_code: str, name: str, price: float,
            shares: int, reason: str = "") -> bool:
        """买入股票"""
        amount = price * shares
        commission = self.calculate_commission(amount, is_sell=False)
        total_cost = amount + commission

        # 检查资金是否足够
        if total_cost > self.portfolio.cash:
            print(f"资金不足: 需要 {total_cost:.2f}, 可用 {self.portfolio.cash:.2f}")
            return False

        # 扣除资金
        self.portfolio.cash -= total_cost

        # 更新持仓
        if ts_code in self.portfolio.positions:
            # 已有持仓，计算新的平均成本
            pos = self.portfolio.positions[ts_code]
            total_shares = pos.shares + shares
            total_cost_basis = pos.avg_price * pos.shares + price * shares
            pos.shares = total_shares
            pos.avg_price = total_cost_basis / total_shares
            pos.current_price = price
        else:
            # 新建持仓
            self.portfolio.positions[ts_code] = Position(
                ts_code=ts_code,
                name=name,
                shares=shares,
                avg_price=price,
                current_price=price
            )

        # 记录交易
        self.portfolio.trade_history.append(TradeRecord(
            date=date,
            action='buy',
            ts_code=ts_code,
            name=name,
            price=price,
            shares=shares,
            amount=amount,
            commission=commission,
            reason=reason
        ))

        return True

    def sell(self, date: str, ts_code: str, name: str, price: float,
             shares: int, reason: str = "") -> bool:
        """卖出股票"""
        # 检查持仓
        if ts_code not in self.portfolio.positions:
            print(f"无持仓: {ts_code}")
            return False

        pos = self.portfolio.positions[ts_code]
        if pos.shares < shares:
            print(f"持仓不足: 持有 {pos.shares}, 卖出 {shares}")
            return False

        amount = price * shares
        commission = self.calculate_commission(amount, is_sell=True)
        total_proceeds = amount - commission

        # 增加资金
        self.portfolio.cash += total_proceeds

        # 更新持仓
        pos.shares -= shares
        pos.current_price = price

        # 如果清仓，移除持仓
        if pos.shares == 0:
            del self.portfolio.positions[ts_code]

        # 记录交易
        self.portfolio.trade_history.append(TradeRecord(
            date=date,
            action='sell',
            ts_code=ts_code,
            name=name,
            price=price,
            shares=shares,
            amount=amount,
            commission=commission,
            reason=reason
        ))

        return True

    def update_positions_price(self, date: str, price_data: Dict[str, float]):
        """更新持仓价格"""
        for ts_code, position in self.portfolio.positions.items():
            if ts_code in price_data:
                position.current_price = price_data[ts_code]

    def record_daily_value(self, date: str):
        """记录每日资产价值"""
        self.portfolio.daily_values.append({
            'date': date,
            'cash': self.portfolio.cash,
            'market_value': self.portfolio.total_market_value,
            'total_assets': self.portfolio.total_assets,
            'return_pct': self.portfolio.total_return_pct
        })

    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        return {
            'cash': self.portfolio.cash,
            'market_value': self.portfolio.total_market_value,
            'total_assets': self.portfolio.total_assets,
            'total_profit_loss': self.portfolio.total_profit_loss,
            'total_return_pct': self.portfolio.total_return_pct,
            'positions_count': len(self.portfolio.positions),
            'trades_count': len(self.portfolio.trade_history)
        }

    def export_results(self) -> Dict:
        """导出结果"""
        return {
            'initial_cash': self.initial_cash,
            'summary': self.get_portfolio_summary(),
            'positions': [asdict(pos) for pos in self.portfolio.positions.values()],
            'trade_history': [asdict(trade) for trade in self.portfolio.trade_history],
            'daily_values': self.portfolio.daily_values
        }


class MarketDataProvider:
    """市场数据提供者"""

    @staticmethod
    def get_trading_dates(start_date: str, end_date: str) -> List[str]:
        """获取交易日列表"""
        try:
            df = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date)
            trading_dates = df[df['is_open'] == 1]['cal_date'].tolist()
            return sorted(trading_dates)
        except Exception as e:
            print(f"获取交易日失败: {e}")
            return []

    @staticmethod
    def get_recent_trading_dates(n_days: int = 10) -> List[str]:
        """获取最近N个交易日"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=n_days * 2)  # 多取一些以确保有足够交易日

        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        dates = MarketDataProvider.get_trading_dates(start_str, end_str)
        return dates[-n_days:] if len(dates) >= n_days else dates

    @staticmethod
    def get_stock_price(ts_code: str, trade_date: str) -> Optional[Dict]:
        """获取股票某日价格"""
        try:
            df = pro.daily(ts_code=ts_code, trade_date=trade_date)
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
    def get_stock_list(limit: int = 50) -> List[Dict]:
        """获取股票列表（按市值排序）"""
        try:
            today = datetime.now().strftime('%Y%m%d')

            # 获取股票基本信息
            df_basic = pro.stock_basic(exchange='', list_status='L',
                                      fields='ts_code,symbol,name,area,industry')

            # 获取市值数据
            df_market = pro.daily_basic(trade_date=today,
                                       fields='ts_code,total_mv,turnover_rate,pe_ttm')

            if df_market.empty:
                # 如果今天没数据，尝试前一个交易日
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                df_market = pro.daily_basic(trade_date=yesterday,
                                           fields='ts_code,total_mv,turnover_rate,pe_ttm')

            # 合并数据
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


if __name__ == '__main__':
    # 测试交易引擎
    print("=" * 60)
    print("交易引擎测试")
    print("=" * 60)

    # 获取最近10个交易日
    trading_dates = MarketDataProvider.get_recent_trading_dates(10)
    print(f"\n最近10个交易日: {trading_dates}")

    # 获取股票列表
    stocks = MarketDataProvider.get_stock_list(limit=10)
    print(f"\n可交易股票: {len(stocks)}只")
    for stock in stocks[:5]:
        print(f"  {stock['ts_code']} {stock['name']} - {stock['industry']}")

    # 初始化交易引擎
    engine = TradingEngine(initial_cash=1000000)
    print(f"\n初始资金: ¥{engine.initial_cash:,.2f}")

    # 模拟交易
    if trading_dates and stocks:
        date = trading_dates[-1]
        stock = stocks[0]

        # 获取价格
        price_data = MarketDataProvider.get_stock_price(stock['ts_code'], date)
        if price_data:
            price = price_data['close']
            shares = 10000

            # 买入
            success = engine.buy(
                date=date,
                ts_code=stock['ts_code'],
                name=stock['name'],
                price=price,
                shares=shares,
                reason="测试买入"
            )

            if success:
                print(f"\n买入成功: {stock['name']} {shares}股 @ ¥{price:.2f}")
                summary = engine.get_portfolio_summary()
                print(f"剩余现金: ¥{summary['cash']:,.2f}")
                print(f"持仓市值: ¥{summary['market_value']:,.2f}")
                print(f"总资产: ¥{summary['total_assets']:,.2f}")

    print("\n" + "=" * 60)
