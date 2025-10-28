"""
测试新的Agent系统 - 使用固定日期
"""
import os
import tushare as ts
from dotenv import load_dotenv

from core import TradingEngine, MarketDataProvider
from tools import TradingTools
from agents import DeepSeekAgent

load_dotenv()

# 配置Tushare
TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()


def test_agent_with_tools():
    """测试Agent和Tools集成"""
    print("=" * 70)
    print("测试AI交易Agent系统")
    print("=" * 70)

    # 创建交易引擎
    engine = TradingEngine(initial_cash=1000000)
    print(f"\n初始资金: {engine.initial_cash:,.2f} 元")

    # 使用固定的交易日（2025年1月第一周）
    trading_dates = ['20250102', '20250103', '20250106', '20250107', '20250108']
    trade_date = trading_dates[-1]  # 使用最后一个交易日
    print(f"交易日期: {trade_date}")

    # 获取股票列表
    stock_pool = MarketDataProvider.get_stock_list(pro, limit=10)
    print(f"股票池: {len(stock_pool)}只")

    # 获取价格数据
    stocks_with_price = []
    for stock in stock_pool:
        price_data = MarketDataProvider.get_stock_price(pro, stock['ts_code'], trade_date)
        if price_data:
            stock_info = stock.copy()
            stock_info.update(price_data)
            stocks_with_price.append(stock_info)

    print(f"有价格数据的股票: {len(stocks_with_price)}只")

    if not stocks_with_price:
        print("\n错误: 无法获取股票价格数据，无法继续测试")
        return

    # 显示前5只股票
    print("\n可交易股票（前5只）:")
    for i, stock in enumerate(stocks_with_price[:5], 1):
        print(f"  {i}. {stock['name']} ({stock['ts_code']}) - {stock['close']:.2f}元")

    # 创建交易工具
    trading_tools = TradingTools(
        engine=engine,
        market_data_provider=None,
        current_date=trade_date,
        available_stocks=stocks_with_price
    )
    tools = trading_tools.get_tools()

    print(f"\n可用工具: {len(tools)}个")
    for tool in tools:
        print(f"  - {tool.name}")

    # 创建Agent
    print("\n创建DeepSeek Agent...")
    try:
        agent = DeepSeekAgent()
        agent.create_agent(tools)
        print("Agent创建成功!")

        # 测试决策
        context = f"""交易日期: {trade_date}

这是你的第一天交易。请分析市场并做出交易决策。

建议流程：
1. 调用 get_portfolio_status 查看当前状态
2. 调用 get_available_stocks 查看可交易股票（建议limit=10）
3. 选择1-2只股票，调用 get_stock_price 查看详细信息
4. 如果合适，使用 buy_stock 买入

注意：
- 买入股数必须是100的倍数
- 建议单只股票投入不超过总资产的30%
- 考虑分散投资"""

        print("\n开始决策...")
        print("-" * 70)

        result = agent.make_decision(context)

        print("-" * 70)
        print("\n决策结果:")
        # 避免编码问题，只打印ASCII可打印字符
        try:
            print(result)
        except UnicodeEncodeError:
            print(result.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

        # 显示最终状态
        print("\n" + "=" * 70)
        summary = engine.get_portfolio_summary()
        print("最终投资组合状态:")
        print(f"  现金: {summary['cash']:,.2f} 元")
        print(f"  市值: {summary['market_value']:,.2f} 元")
        print(f"  总资产: {summary['total_assets']:,.2f} 元")
        print(f"  持仓数: {summary['positions_count']}")
        print(f"  交易次数: {summary['trades_count']}")

        # 显示持仓详情
        if engine.portfolio.positions:
            print("\n持仓详情:")
            for ts_code, pos in engine.portfolio.positions.items():
                print(f"  {pos.name} ({ts_code}): {pos.shares}股 @ {pos.avg_price:.2f}元")

        # 显示交易记录
        if engine.portfolio.trade_history:
            print("\n交易记录:")
            for trade in engine.portfolio.trade_history:
                print(f"  {trade.action.upper()} {trade.name}: {trade.shares}股 @ {trade.price:.2f}元")
                print(f"    理由: {trade.reason[:50]}...")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70)


if __name__ == '__main__':
    test_agent_with_tools()
