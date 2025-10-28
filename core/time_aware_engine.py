"""
时间感知的交易引擎 - 确保AI只能看到历史数据
"""
from typing import Dict, List, Optional
from core.engine import TradingEngine, Portfolio
from core.market_data import MarketDataProvider
from core.agent_state import AgentStateManager


class TimeAwareTradingEngine(TradingEngine):
    """时间感知的交易引擎"""

    def __init__(self, agent_name: str, initial_capital: float, market_data: MarketDataProvider):
        """
        初始化时间感知交易引擎

        Args:
            agent_name: Agent名称
            initial_capital: 初始资金
            market_data: 市场数据提供者
        """
        super().__init__(initial_capital)
        self.agent_name = agent_name
        self.market_data = market_data
        self.state_manager = AgentStateManager(agent_name)

        # 当前模拟日期（AI只能看到这个日期及之前的数据）
        self.current_simulation_date = None

    def initialize_simulation(self, start_date: str):
        """
        初始化模拟交易

        Args:
            start_date: 开始日期 YYYYMMDD
        """
        self.current_simulation_date = start_date
        self.state_manager.initialize_simulation(start_date)

        # 重置交易引擎状态
        self.portfolio = Portfolio(
            cash=self.initial_cash,
            positions={},
            trade_history=[],
            daily_values=[],
            initial_capital=self.initial_cash
        )

    def advance_to_date(self, new_date: str):
        """
        推进到新的交易日

        Args:
            new_date: 新日期 YYYYMMDD
        """
        # 保存前一天的快照
        if self.current_simulation_date:
            self._save_daily_snapshot()

        # 推进日期
        self.current_simulation_date = new_date
        self.state_manager.advance_to_date(new_date)

    def get_available_data_cutoff_date(self) -> str:
        """
        获取AI可以访问的数据截止日期

        Returns:
            当前模拟日期（AI只能看到这个日期及之前的数据）
        """
        return self.current_simulation_date

    def buy(self, date: str, ts_code: str, name: str, price: float, shares: int, reason: str = "") -> bool:
        """
        买入股票（覆盖父类方法，添加状态持久化）

        Args:
            date: 交易日期（必须等于当前模拟日期）
            ts_code: 股票代码
            name: 股票名称
            price: 买入价格
            shares: 买入股数
            reason: 买入原因

        Returns:
            是否成功
        """
        # 检查日期是否合法
        if date != self.current_simulation_date:
            print(f"错误: 不能在未来日期 {date} 交易（当前日期: {self.current_simulation_date}）")
            return False

        # 执行买入
        success = super().buy(date, ts_code, name, price, shares, reason)

        if success:
            # 记录交易
            self.state_manager.record_trade({
                "action": "buy",
                "ts_code": ts_code,
                "name": name,
                "price": price,
                "shares": shares,
                "reason": reason
            })

            # 更新持仓
            position = self.portfolio.positions.get(ts_code)
            if position:
                self.state_manager.update_position(
                    ts_code,
                    position.shares,
                    position.avg_price
                )

            # 更新资金
            self.state_manager.update_capital(self.portfolio.cash)

        return success

    def sell(self, date: str, ts_code: str, name: str, price: float, shares: int, reason: str = "") -> bool:
        """
        卖出股票（覆盖父类方法，添加状态持久化）

        Args:
            date: 交易日期（必须等于当前模拟日期）
            ts_code: 股票代码
            name: 股票名称
            price: 卖出价格
            shares: 卖出股数
            reason: 卖出原因

        Returns:
            是否成功
        """
        # 检查日期是否合法
        if date != self.current_simulation_date:
            print(f"错误: 不能在未来日期 {date} 交易（当前日期: {self.current_simulation_date}）")
            return False

        # 执行卖出
        success = super().sell(date, ts_code, name, price, shares, reason)

        if success:
            # 记录交易
            self.state_manager.record_trade({
                "action": "sell",
                "ts_code": ts_code,
                "name": name,
                "price": price,
                "shares": shares,
                "reason": reason
            })

            # 更新持仓
            position = self.portfolio.positions.get(ts_code)
            if position:
                self.state_manager.update_position(
                    ts_code,
                    position.shares,
                    position.avg_price
                )
            else:
                # 已清仓
                self.state_manager.update_position(ts_code, 0, 0)

            # 更新资金
            self.state_manager.update_capital(self.portfolio.cash)

        return success

    def _save_daily_snapshot(self):
        """保存每日快照"""
        # 计算持仓市值
        positions_value = 0
        for ts_code, position in self.portfolio.positions.items():
            # 获取当日收盘价
            price_data = self.market_data.get_stock_price_from_json(
                ts_code,
                self.current_simulation_date
            )
            if price_data:
                positions_value += position.shares * price_data['close']

        total_value = self.portfolio.cash + positions_value

        # 保存快照
        self.state_manager.save_daily_snapshot(total_value, positions_value)

    def get_summary(self) -> Dict:
        """获取汇总信息"""
        # 计算当前市值
        positions_value = 0
        for ts_code, position in self.portfolio.positions.items():
            price_data = self.market_data.get_stock_price_from_json(
                ts_code,
                self.current_simulation_date
            )
            if price_data:
                positions_value += position.shares * price_data['close']

        total_value = self.portfolio.cash + positions_value

        return {
            **self.state_manager.get_summary(),
            "current_cash": self.portfolio.cash,
            "positions_value": positions_value,
            "total_value": total_value,
            "return_rate": (total_value - self.initial_cash) / self.initial_cash * 100
        }
