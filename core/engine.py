"""
交易引擎核心
"""
from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class Position:
    """持仓信息"""
    ts_code: str
    name: str
    shares: int
    avg_price: float
    current_price: float

    @property
    def market_value(self) -> float:
        return self.shares * self.current_price

    @property
    def profit_loss(self) -> float:
        return (self.current_price - self.avg_price) * self.shares

    @property
    def profit_loss_pct(self) -> float:
        if self.avg_price == 0:
            return 0
        return ((self.current_price - self.avg_price) / self.avg_price) * 100


@dataclass
class TradeRecord:
    """交易记录"""
    date: str
    action: str
    ts_code: str
    name: str
    price: float
    shares: int
    amount: float
    commission: float
    reason: str


@dataclass
class Portfolio:
    """投资组合"""
    cash: float
    positions: Dict[str, Position]
    trade_history: List[TradeRecord]
    daily_values: List[Dict]

    @property
    def total_market_value(self) -> float:
        return sum(pos.market_value for pos in self.positions.values())

    @property
    def total_assets(self) -> float:
        return self.cash + self.total_market_value

    @property
    def total_profit_loss(self) -> float:
        if not self.daily_values:
            return 0
        initial_value = self.daily_values[0]['total_assets']
        return self.total_assets - initial_value

    @property
    def total_return_pct(self) -> float:
        if not self.daily_values:
            return 0
        initial_value = self.daily_values[0]['total_assets']
        if initial_value == 0:
            return 0
        return ((self.total_assets - initial_value) / initial_value) * 100


class TradingEngine:
    """交易引擎"""

    COMMISSION_RATE = 0.0003
    MIN_COMMISSION = 5
    STAMP_TAX_RATE = 0.001

    def __init__(self, initial_cash: float = 1000000):
        self.initial_cash = initial_cash
        self.portfolio = Portfolio(
            cash=initial_cash,
            positions={},
            trade_history=[],
            daily_values=[]
        )

    def calculate_commission(self, amount: float, is_sell: bool = False) -> float:
        commission = max(amount * self.COMMISSION_RATE, self.MIN_COMMISSION)
        if is_sell:
            stamp_tax = amount * self.STAMP_TAX_RATE
            commission += stamp_tax
        return commission

    def buy(self, date: str, ts_code: str, name: str, price: float,
            shares: int, reason: str = "") -> bool:
        amount = price * shares
        commission = self.calculate_commission(amount, is_sell=False)
        total_cost = amount + commission

        if total_cost > self.portfolio.cash:
            return False

        self.portfolio.cash -= total_cost

        if ts_code in self.portfolio.positions:
            pos = self.portfolio.positions[ts_code]
            total_shares = pos.shares + shares
            total_cost_basis = pos.avg_price * pos.shares + price * shares
            pos.shares = total_shares
            pos.avg_price = total_cost_basis / total_shares
            pos.current_price = price
        else:
            self.portfolio.positions[ts_code] = Position(
                ts_code=ts_code,
                name=name,
                shares=shares,
                avg_price=price,
                current_price=price
            )

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
        if ts_code not in self.portfolio.positions:
            return False

        pos = self.portfolio.positions[ts_code]
        if pos.shares < shares:
            return False

        amount = price * shares
        commission = self.calculate_commission(amount, is_sell=True)
        total_proceeds = amount - commission

        self.portfolio.cash += total_proceeds

        pos.shares -= shares
        pos.current_price = price

        if pos.shares == 0:
            del self.portfolio.positions[ts_code]

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
        for ts_code, position in self.portfolio.positions.items():
            if ts_code in price_data:
                position.current_price = price_data[ts_code]

    def record_daily_value(self, date: str):
        self.portfolio.daily_values.append({
            'date': date,
            'cash': self.portfolio.cash,
            'market_value': self.portfolio.total_market_value,
            'total_assets': self.portfolio.total_assets,
            'return_pct': self.portfolio.total_return_pct
        })

    def get_portfolio_summary(self) -> Dict:
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
        return {
            'initial_cash': self.initial_cash,
            'summary': self.get_portfolio_summary(),
            'positions': [asdict(pos) for pos in self.portfolio.positions.values()],
            'trade_history': [asdict(trade) for trade in self.portfolio.trade_history],
            'daily_values': self.portfolio.daily_values
        }
