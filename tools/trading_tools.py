"""
交易工具集
供AI Agent调用的交易工具
"""
from typing import Optional, Dict, List, Any
from langchain.tools import tool


class TradingTools:
    """交易工具集合"""

    def __init__(self, engine, market_data_provider, current_date: str, available_stocks: List[Dict]):
        self.engine = engine
        self.market_data = market_data_provider
        self.current_date = current_date
        self.available_stocks = available_stocks
        self._stock_price_cache = {}

    def _get_stock_info(self, ts_code: str) -> Optional[Dict]:
        """获取股票信息"""
        for stock in self.available_stocks:
            if stock['ts_code'] == ts_code:
                return stock
        return None

    def get_tools(self):
        """返回工具列表"""

        @tool
        def get_portfolio_status() -> str:
            """
            获取当前投资组合状态，包括现金、持仓、总资产等信息。

            Returns:
                str: 投资组合详细信息
            """
            summary = self.engine.get_portfolio_summary()

            result = f"投资组合状态:\n"
            result += f"- 现金: ¥{summary['cash']:,.2f}\n"
            result += f"- 持仓市值: ¥{summary['market_value']:,.2f}\n"
            result += f"- 总资产: ¥{summary['total_assets']:,.2f}\n"
            result += f"- 收益率: {summary['total_return_pct']:.2f}%\n"
            result += f"- 持仓数量: {summary['positions_count']}只\n"
            result += f"- 交易次数: {summary['trades_count']}次\n\n"

            if self.engine.portfolio.positions:
                result += "当前持仓:\n"
                for ts_code, pos in self.engine.portfolio.positions.items():
                    result += f"  {pos.name} ({pos.ts_code}): {pos.shares}股, "
                    result += f"成本¥{pos.avg_price:.2f}, 现价¥{pos.current_price:.2f}, "
                    result += f"盈亏{pos.profit_loss_pct:+.2f}%\n"
            else:
                result += "当前无持仓\n"

            return result

        @tool
        def get_available_stocks(limit: int = 20) -> str:
            """
            获取可交易的股票列表。

            Args:
                limit: 返回的股票数量，默认20只

            Returns:
                str: 股票列表信息
            """
            stocks = self.available_stocks[:limit]
            result = f"可交易股票 (前{len(stocks)}只):\n"

            for i, stock in enumerate(stocks, 1):
                result += f"{i}. {stock['name']} ({stock['ts_code']}) - {stock['industry']}\n"
                if 'close' in stock:
                    result += f"   价格: ¥{stock['close']:.2f}, 涨跌: {stock.get('change', 0):+.2f}%\n"

            return result

        @tool
        def get_stock_price(ts_code: str) -> str:
            """
            获取指定股票的当前价格和基本信息。

            Args:
                ts_code: 股票代码，如 '600000.SH'

            Returns:
                str: 股票价格信息
            """
            # 先从缓存中查找
            if ts_code in self._stock_price_cache:
                stock = self._stock_price_cache[ts_code]
            else:
                # 从available_stocks中查找
                stock = self._get_stock_info(ts_code)
                if stock:
                    self._stock_price_cache[ts_code] = stock

            if not stock:
                return f"错误: 未找到股票 {ts_code}"

            result = f"股票信息:\n"
            result += f"代码: {stock['ts_code']}\n"
            result += f"名称: {stock['name']}\n"
            result += f"行业: {stock.get('industry', '未知')}\n"

            if 'close' in stock:
                result += f"当前价格: ¥{stock['close']:.2f}\n"
                result += f"涨跌幅: {stock.get('change', 0):+.2f}%\n"
                result += f"最高: ¥{stock.get('high', 0):.2f}\n"
                result += f"最低: ¥{stock.get('low', 0):.2f}\n"

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

            # 获取股票信息
            stock = self._get_stock_info(ts_code)
            if not stock:
                return f"错误: 未找到股票 {ts_code}"

            if 'close' not in stock:
                return f"错误: 股票 {ts_code} 无价格数据"

            price = stock['close']
            name = stock['name']

            # 执行买入
            success = self.engine.buy(
                date=self.current_date,
                ts_code=ts_code,
                name=name,
                price=price,
                shares=shares,
                reason=reason
            )

            if success:
                cost = price * shares
                commission = self.engine.calculate_commission(cost, is_sell=False)
                total_cost = cost + commission

                return (f"买入成功!\n"
                       f"股票: {name} ({ts_code})\n"
                       f"价格: ¥{price:.2f}\n"
                       f"股数: {shares}\n"
                       f"成本: ¥{cost:,.2f}\n"
                       f"手续费: ¥{commission:.2f}\n"
                       f"总计: ¥{total_cost:,.2f}\n"
                       f"剩余现金: ¥{self.engine.portfolio.cash:,.2f}")
            else:
                return (f"买入失败!\n"
                       f"可能原因: 现金不足\n"
                       f"需要: ¥{price * shares + self.engine.calculate_commission(price * shares):,.2f}\n"
                       f"可用: ¥{self.engine.portfolio.cash:,.2f}")

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

            pos = self.engine.portfolio.positions[ts_code]
            if pos.shares < shares:
                return f"错误: 持仓不足，持有{pos.shares}股，尝试卖出{shares}股"

            # 获取当前价格
            stock = self._get_stock_info(ts_code)
            if not stock or 'close' not in stock:
                return f"错误: 无法获取股票价格"

            price = stock['close']
            name = stock['name']

            # 执行卖出
            success = self.engine.sell(
                date=self.current_date,
                ts_code=ts_code,
                name=name,
                price=price,
                shares=shares,
                reason=reason
            )

            if success:
                proceeds = price * shares
                commission = self.engine.calculate_commission(proceeds, is_sell=True)
                net_proceeds = proceeds - commission

                return (f"卖出成功!\n"
                       f"股票: {name} ({ts_code})\n"
                       f"价格: ¥{price:.2f}\n"
                       f"股数: {shares}\n"
                       f"收入: ¥{proceeds:,.2f}\n"
                       f"手续费: ¥{commission:.2f}\n"
                       f"净收入: ¥{net_proceeds:,.2f}\n"
                       f"现金: ¥{self.engine.portfolio.cash:,.2f}")
            else:
                return "卖出失败!"

        return [
            get_portfolio_status,
            get_available_stocks,
            get_stock_price,
            buy_stock,
            sell_stock
        ]
