"""
测试新的Agent系统
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

    # 获取最近一个交易日
    trading_dates = MarketDataProvider.get_recent_trading_dates(pro, n_days=1)
    if not trading_dates:
        print("无法获取交易日")
        return

    trade_date = trading_dates[0]
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
        print(f"  - {tool.name}: {tool.description[:60]}...")

    # 创建Agent
    print("\n创建DeepSeek Agent...")
    try:
        agent = DeepSeekAgent()
        agent.create_agent(tools)
        print("Agent创建成功!")

        # 测试决策
        context = f"""交易日期: {trade_date}

这是你的第一天交易。请使用提供的工具：
1. 查看投资组合状态
2. 查看可交易的股票列表
3. 分析并决定是否买入某只股票

注意：买入股数必须是100的倍数。"""

        print("\n开始决策...")
        print("-" * 70)

        result = agent.make_decision(context)

        print("-" * 70)
        print("\n决策结果:")
        print(result)

        # 显示最终状态
        print("\n" + "=" * 70)
        summary = engine.get_portfolio_summary()
        print("最终投资组合状态:")
        print(f"  现金: {summary['cash']:,.2f} 元")
        print(f"  市值: {summary['market_value']:,.2f} 元")
        print(f"  总资产: {summary['total_assets']:,.2f} 元")
        print(f"  持仓数: {summary['positions_count']}")
        print(f"  交易次数: {summary['trades_count']}")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70)


if __name__ == '__main__':
    test_agent_with_tools()
