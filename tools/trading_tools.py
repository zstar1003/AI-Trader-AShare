"""
交易工具集
供AI Agent调用的交易工具 - 时间感知版本
"""
from typing import Optional, Dict, List
from langchain.tools import tool


class TradingToolkit:
    """时间感知的交易工具集"""

    def __init__(self, engine, market_data_provider, current_date: str):
        """
        初始化交易工具集

        Args:
            engine: 时间感知交易引擎
            market_data_provider: 市场数据提供者
            current_date: 当前日期 YYYYMMDD
        """
        self.engine = engine
        self.market_data = market_data_provider
        self.current_date = current_date
        self._stock_cache = {}

    def update_current_date(self, new_date: str):
        """更新当前日期"""
        self.current_date = new_date
        self._stock_cache = {}  # 清空缓存

    def _get_stock_price(self, ts_code: str) -> Optional[Dict]:
        """
        获取股票价格（只能获取当前日期及之前的数据）

        Returns:
            Dict: 包含 open, close, high, low, volume, change
        """
        if ts_code in self._stock_cache:
            return self._stock_cache[ts_code]

        # 从JSON文件读取
        price_data = self.market_data.get_stock_price_from_json(ts_code, self.current_date)

        if price_data:
            self._stock_cache[ts_code] = price_data

        return price_data

    def get_tools(self):
        """返回工具列表"""

        @tool
        def get_portfolio_status() -> str:
            """
            获取当前投资组合状态，包括现金、持仓、总资产等信息。

            Returns:
                str: 投资组合详细信息
            """
            # 计算持仓市值
            positions_value = 0
            for ts_code, position in self.engine.portfolio.positions.items():
                price_data = self._get_stock_price(ts_code)
                if price_data:
                    positions_value += position.shares * price_data['close']

            total_value = self.engine.portfolio.cash + positions_value
            return_rate = (total_value - self.engine.portfolio.initial_capital) / self.engine.portfolio.initial_capital * 100

            result = f"投资组合状态 (截至{self.current_date[:4]}-{self.current_date[4:6]}-{self.current_date[6:]}):\n"
            result += f"- 现金: {self.engine.portfolio.cash:,.2f} RMB\n"
            result += f"- 持仓市值: {positions_value:,.2f} RMB\n"
            result += f"- 总资产: {total_value:,.2f} RMB\n"
            result += f"- 收益率: {return_rate:.2f}%\n"
            result += f"- 持仓数量: {len(self.engine.portfolio.positions)}只\n"
            result += f"- 交易次数: {len(self.engine.portfolio.trade_history)}次\n\n"

            if self.engine.portfolio.positions:
                result += "当前持仓:\n"
                for ts_code, position in self.engine.portfolio.positions.items():
                    price_data = self._get_stock_price(ts_code)
                    if price_data:
                        current_price = price_data['close']
                        position_value = position.shares * current_price
                        profit = position_value - (position.shares * position.avg_price)
                        profit_rate = profit / (position.shares * position.avg_price) * 100

                        result += f"  {ts_code}: {position.shares}股\n"
                        result += f"    成本: {position.avg_price:.2f} RMB, 现价: {current_price:.2f} RMB\n"
                        result += f"    市值: {position_value:,.2f} RMB, 盈亏: {profit:+,.2f} RMB ({profit_rate:+.2f}%)\n"
            else:
                result += "当前无持仓\n"

            return result

        @tool
        def get_available_stocks(limit: int = 50) -> str:
            """
            获取可交易的A股列表（有历史数据的股票）。

            Args:
                limit: 返回的股票数量，默认50只

            Returns:
                str: 股票列表信息
            """
            # 获取所有有JSON数据的股票
            all_stocks = self.market_data.get_all_stocks_from_json()

            if not all_stocks:
                return "错误: 未找到可交易股票"

            # 只返回前limit只
            stocks = all_stocks[:limit]

            result = f"可交易股票 (共{len(all_stocks)}只，显示前{len(stocks)}只):\n\n"

            for i, ts_code in enumerate(stocks, 1):
                # 获取当前价格
                price_data = self._get_stock_price(ts_code)
                if price_data:
                    result += f"{i}. {ts_code}\n"
                    result += f"   价格: {price_data['close']:.2f} RMB, "
                    result += f"涨跌: {price_data.get('change', 0):+.2f}%\n"

            return result

        @tool
        def get_stock_price(ts_code: str) -> str:
            """
            获取指定股票的当前价格和基本信息（只能看到当前日期的数据）。

            Args:
                ts_code: 股票代码，如 '600000.SH'

            Returns:
                str: 股票价格信息
            """
            price_data = self._get_stock_price(ts_code)

            if not price_data:
                return f"错误: 未找到股票 {ts_code} 在日期 {self.current_date} 的价格数据"

            result = f"股票价格 ({self.current_date[:4]}-{self.current_date[4:6]}-{self.current_date[6:]}):\n"
            result += f"代码: {ts_code}\n"
            result += f"日期: {price_data['date']}\n"
            result += f"开盘: {price_data['open']:.2f} RMB\n"
            result += f"最高: {price_data['high']:.2f} RMB\n"
            result += f"最低: {price_data['low']:.2f} RMB\n"
            result += f"收盘: {price_data['close']:.2f} RMB\n"
            result += f"成交量: {price_data['volume']:,.0f}\n"

            return result

        @tool
        def buy_stock(ts_code: str, shares: int, reason: str = "") -> str:
            """
            买入股票。买入前请确保有足够的现金。

            Args:
                ts_code: 股票代码，如 '600000.SH'
                shares: 买入股数，必须是100的倍数
                reason: 买入理由

            Returns:
                str: 交易结果
            """
            # 验证股数
            if shares <= 0 or shares % 100 != 0:
                return f"错误: 股数必须是100的正整数倍，当前: {shares}"

            # 获取价格
            price_data = self._get_stock_price(ts_code)
            if not price_data:
                return f"错误: 未找到股票 {ts_code} 的价格数据"

            price = price_data['close']

            # 执行买入
            success = self.engine.buy(
                date=self.current_date,
                ts_code=ts_code,
                name=ts_code,
                price=price,
                shares=shares,
                reason=reason
            )

            if success:
                cost = price * shares
                commission = self.engine.calculate_commission(cost, is_sell=False)
                total_cost = cost + commission

                return (f"买入成功!\n"
                       f"股票: {ts_code}\n"
                       f"价格: {price:.2f} RMB\n"
                       f"股数: {shares}\n"
                       f"成本: {cost:,.2f} RMB\n"
                       f"手续费: {commission:.2f} RMB\n"
                       f"总计: {total_cost:,.2f} RMB\n"
                       f"剩余现金: {self.engine.portfolio.cash:,.2f} RMB")
            else:
                needed = price * shares + self.engine.calculate_commission(price * shares, is_sell=False)
                return (f"买入失败!\n"
                       f"可能原因: 现金不足\n"
                       f"需要: {needed:,.2f} RMB\n"
                       f"可用: {self.engine.portfolio.cash:,.2f} RMB")

        @tool
        def sell_stock(ts_code: str, shares: int, reason: str = "") -> str:
            """
            卖出股票。卖出前请确保有足够的持仓。

            Args:
                ts_code: 股票代码，如 '600000.SH'
                shares: 卖出股数，必须是100的倍数
                reason: 卖出理由

            Returns:
                str: 交易结果
            """
            # 验证股数
            if shares <= 0 or shares % 100 != 0:
                return f"错误: 股数必须是100的正整数倍，当前: {shares}"

            # 检查持仓
            if ts_code not in self.engine.portfolio.positions:
                return f"错误: 无持仓 {ts_code}"

            position = self.engine.portfolio.positions[ts_code]
            if position.shares < shares:
                return f"错误: 持仓不足，持有{position.shares}股，尝试卖出{shares}股"

            # 获取当前价格
            price_data = self._get_stock_price(ts_code)
            if not price_data:
                return f"错误: 无法获取股票价格"

            price = price_data['close']

            # 执行卖出
            success = self.engine.sell(
                date=self.current_date,
                ts_code=ts_code,
                name=ts_code,
                price=price,
                shares=shares,
                reason=reason
            )

            if success:
                proceeds = price * shares
                commission = self.engine.calculate_commission(proceeds, is_sell=True)
                net_proceeds = proceeds - commission

                return (f"卖出成功!\n"
                       f"股票: {ts_code}\n"
                       f"价格: {price:.2f} RMB\n"
                       f"股数: {shares}\n"
                       f"收入: {proceeds:,.2f} RMB\n"
                       f"手续费: {commission:.2f} RMB\n"
                       f"净收入: {net_proceeds:,.2f} RMB\n"
                       f"现金: {self.engine.portfolio.cash:,.2f} RMB")
            else:
                return "卖出失败!"

        return [
            get_portfolio_status,
            get_available_stocks,
            get_stock_price,
            buy_stock,
            sell_stock
        ]
