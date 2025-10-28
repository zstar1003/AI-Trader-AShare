"""
10天模拟交易 - 时间感知版本
AI只能看到当前日期及之前的数据
"""
import os
import sys
from dotenv import load_dotenv
import tushare as ts
from datetime import datetime

from core.market_data import MarketDataProvider
from core.time_aware_engine import TimeAwareTradingEngine
from tools.trading_tools import TradingToolkit
from agents.llm_agents import DeepSeekAgent

load_dotenv()

# 初始化Tushare
TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()

# 初始化市场数据提供者
market_data = MarketDataProvider(pro)


def get_recent_trading_dates(n_days: int = 10):
    """获取最近N个交易日"""
    dates = MarketDataProvider.get_recent_trading_dates(pro, n_days=n_days + 5)
    # 返回最近10天
    return dates[-n_days:]


def simulate_trading(agent_name: str = "DeepSeek_Trader"):
    """
    模拟10天交易

    Args:
        agent_name: Agent名称
    """
    print("=" * 80)
    print(f"开始10天模拟交易 - {agent_name}")
    print("=" * 80)

    # 获取最近10个交易日
    trading_dates = get_recent_trading_dates(10)
    print(f"\n模拟交易日期:")
    for i, date in enumerate(trading_dates, 1):
        formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        print(f"  Day {i}: {formatted_date}")

    # 初始化时间感知交易引擎
    engine = TimeAwareTradingEngine(
        agent_name=agent_name,
        initial_capital=1000000.0,
        market_data=market_data
    )

    # 初始化模拟（从第一天开始）
    start_date = trading_dates[0]
    engine.initialize_simulation(start_date)
    print(f"\n初始化完成: 起始日期 {start_date}, 初始资金 1,000,000 RMB")

    # 创建Agent
    agent = DeepSeekAgent(name=agent_name)

    # 创建Trading Toolkit
    toolkit = TradingToolkit(
        engine=engine,
        market_data_provider=market_data,
        current_date=start_date  # 初始日期
    )

    # 初始化Agent（创建agent实例）
    agent.create_agent(toolkit.get_tools())

    # 逐日模拟
    for day_index, current_date in enumerate(trading_dates, 1):
        print("\n" + "=" * 80)
        print(f"Day {day_index}/{len(trading_dates)}: {current_date[:4]}-{current_date[4:6]}-{current_date[6:]}")
        print("=" * 80)

        # 推进到当前日期
        engine.advance_to_date(current_date)
        toolkit.update_current_date(current_date)

        # 显示当前状态
        summary = engine.get_summary()
        print(f"\n当前状态:")
        print(f"  现金: {summary['current_cash']:,.2f} RMB")
        print(f"  持仓市值: {summary['positions_value']:,.2f} RMB")
        print(f"  总资产: {summary['total_value']:,.2f} RMB")
        print(f"  收益率: {summary['return_rate']:.2f}%")

        # Agent决策
        print(f"\n{agent_name} 正在分析市场...")

        # 创建提示词
        prompt = f"""
今天是 {current_date[:4]}年{current_date[4:6]}月{current_date[6:]}日。

你的任务是基于今天及之前的市场数据做出交易决策。

重要提醒:
1. 你只能看到今天（{current_date}）及之前的数据
2. 不能看到未来的数据
3. 当前持仓信息和资金状况请使用 get_portfolio_status 工具获取
4. 可用股票列表使用 get_available_stocks 工具获取
5. 查询股票价格使用 get_stock_price 工具

请分析市场并做出交易决策。如果发现好的投资机会就买入，如果持仓需要调整就卖出。
"""

        try:
            # Agent执行决策
            result = agent.make_decision(prompt)
            print(f"\nAgent决策结果:")
            print(result)

        except Exception as e:
            print(f"\nAgent执行出错: {e}")
            import traceback
            traceback.print_exc()

        # 显示今日交易
        trades_today = [t for t in engine.portfolio.trade_history if t.date == current_date]
        if trades_today:
            print(f"\n今日交易记录:")
            for trade in trades_today:
                action = "买入" if trade.action == "buy" else "卖出"
                print(f"  {action} {trade.name}({trade.ts_code}): "
                      f"{trade.shares}股 @ {trade.price:.2f} RMB")
                if trade.reason:
                    print(f"    原因: {trade.reason}")
        else:
            print(f"\n今日无交易")

        # 小延迟（避免API限流）
        import time
        time.sleep(1)

    # 模拟结束
    print("\n" + "=" * 80)
    print("模拟交易结束")
    print("=" * 80)

    final_summary = engine.get_summary()
    print(f"\n最终结果:")
    print(f"  初始资金: {final_summary['initial_capital']:,.2f} RMB")
    print(f"  最终现金: {final_summary['current_cash']:,.2f} RMB")
    print(f"  持仓市值: {final_summary['positions_value']:,.2f} RMB")
    print(f"  总资产: {final_summary['total_value']:,.2f} RMB")
    print(f"  总收益率: {final_summary['return_rate']:.2f}%")
    print(f"  交易次数: {final_summary['trades_count']}")

    # 显示持仓
    if engine.portfolio.positions:
        print(f"\n最终持仓:")
        for ts_code, position in engine.portfolio.positions.items():
            current_price_data = market_data.get_stock_price_from_json(ts_code, trading_dates[-1])
            if current_price_data:
                current_value = position.shares * current_price_data['close']
                profit = current_value - (position.shares * position.avg_price)
                profit_rate = profit / (position.shares * position.avg_price) * 100

                print(f"  {ts_code}: {position.shares}股 @ {position.avg_price:.2f} RMB")
                print(f"    当前价: {current_price_data['close']:.2f} RMB")
                print(f"    市值: {current_value:,.2f} RMB")
                print(f"    盈亏: {profit:,.2f} RMB ({profit_rate:.2f}%)")

    # 保存状态文件信息
    print(f"\n状态文件已保存: data/agent_data/{agent_name}_state.json")


if __name__ == "__main__":
    simulate_trading("DeepSeek_Trader")
