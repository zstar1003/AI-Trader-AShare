"""
10天模拟交易 - 支持多Agent运行
AI只能看到当前日期及之前的数据
"""
import os
import time
import tushare as ts

from dotenv import load_dotenv
from core.market_data import MarketDataProvider
from core.time_aware_engine import TimeAwareTradingEngine
from tools.trading_tools import TradingToolkit
from agents.llm_agents import DeepSeekAgent, GLMAgent, KimiAgent, RingAgent

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


# Agent配置
AVAILABLE_AGENTS = {
    'deepseek': {
        'class': DeepSeekAgent,
        'name': 'DeepSeek_Trader',
        'display_name': 'DeepSeek',
        'enabled': True
    },
    'glm': {
        'class': GLMAgent,
        'name': 'GLM_Trader',
        'display_name': 'GLM',
        'enabled': True
    },
    'kimi': {
        'class': KimiAgent,
        'name': 'Kimi_Trader',
        'display_name': 'Kimi',
        'enabled': True
    },
    'ring': {
        'class': RingAgent,
        'name': 'Ring_Trader',
        'display_name': 'Ring',
        'enabled': True
    }
}


def simulate_trading(agent_key: str):
    """
    模拟单个Agent的10天交易

    Args:
        agent_key: Agent的key（如 'deepseek', 'gpt4' 等）
    """
    agent_config = AVAILABLE_AGENTS.get(agent_key)
    if not agent_config:
        print(f"错误: 未找到Agent配置 '{agent_key}'")
        return

    agent_name = agent_config['name']
    display_name = agent_config['display_name']

    print("=" * 80)
    print(f"开始10天模拟交易 - {display_name}")
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
    try:
        agent = agent_config['class'](name=display_name)
    except ValueError as e:
        print(f"错误: 无法创建Agent - {e}")
        print(f"提示: 请在 .env 文件中配置相应的API密钥")
        return

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
        print(f"\n{display_name} 正在分析市场...")

        # 创建提示词
        prompt = f"""
今天是 {current_date[:4]}年{current_date[4:6]}月{current_date[6:]}日。

你的任务是基于今天及之前的市场数据做出交易决策。

重要提醒:
1. 你只能看到今天（{current_date}）及之前的数据
2. 不能看到未来的数据
3. 初始资金: 1,000,000 RMB

可用工具说明:
- get_portfolio_status: 查看当前持仓、资金、收益等信息
- get_available_stocks: 获取所有可交易股票代码列表（5000+只）
- search_stocks: 按条件筛选股票（涨跌幅、价格区间、成交量等）
- get_stock_price: 获取指定股票的详细价格信息
- buy_stock: 买入股票
- sell_stock: 卖出股票

交易策略建议:
1. 先查看当前持仓状态 (get_portfolio_status)
2. 使用 search_stocks 筛选出符合条件的股票（如涨幅较大、跌幅较大、成交活跃等）
3. 对感兴趣的股票使用 get_stock_price 获取详细信息
4. 根据分析结果做出买入或卖出决策

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


def simulate_all_agents(agent_keys=None):
    """
    运行多个Agent的模拟

    Args:
        agent_keys: Agent key列表，如果为None则运行所有enabled的Agent
    """
    if agent_keys is None:
        # 运行所有enabled的Agent
        agent_keys = [key for key, config in AVAILABLE_AGENTS.items() if config['enabled']]

    if not agent_keys:
        print("Error: No enabled agents")
        print("\nAvailable Agents:")
        for key, config in AVAILABLE_AGENTS.items():
            status = "[ENABLED]" if config['enabled'] else "[DISABLED]"
            print(f"  {key}: {config['display_name']} - {status}")
        return

    print(f"\nPreparing to run {len(agent_keys)} agent(s)")
    print("Agent list:", ", ".join([AVAILABLE_AGENTS[k]['display_name'] for k in agent_keys]))
    print()

    for i, agent_key in enumerate(agent_keys, 1):
        print(f"\n{'#' * 80}")
        print(f"# Agent {i}/{len(agent_keys)}")
        print(f"{'#' * 80}\n")

        simulate_trading(agent_key)

        # Agent之间的间隔
        if i < len(agent_keys):
            print("\n" + "-" * 80)
            print("Waiting 5 seconds before next agent...")
            print("-" * 80)
            import time
            time.sleep(5)

    print("\n" + "=" * 80)
    print("All agent simulations completed!")
    print("=" * 80)
    print(f"\nData files location: data/agent_data/")
    print("Copy data to docs directory:")
    print("  python scripts/copy_data_to_docs.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='AI交易模拟 - 支持多Agent')
    parser.add_argument('--agent', type=str, help='运行指定的Agent (deepseek/gpt4/claude/qwen3)')
    parser.add_argument('--agents', type=str, help='运行多个Agent，逗号分隔 (例: deepseek,gpt4)')
    parser.add_argument('--all', action='store_true', help='运行所有已启用的Agent')
    parser.add_argument('--list', action='store_true', help='列出所有可用的Agent')

    args = parser.parse_args()

    if args.list:
        print("Available Agents:")
        print()
        for key, config in AVAILABLE_AGENTS.items():
            status = "[ENABLED]" if config['enabled'] else "[DISABLED]"
            print(f"  {key:10} - {config['display_name']:15} {status}")
            if not config['enabled']:
                print(f"             Note: Requires API key in .env")
        print()
        print("Usage examples:")
        print("  python run_simulation.py --agent deepseek")
        print("  python run_simulation.py --agents deepseek,gpt4")
        print("  python run_simulation.py --all")
    elif args.all:
        simulate_all_agents()
    elif args.agents:
        agent_keys = [k.strip() for k in args.agents.split(',')]
        simulate_all_agents(agent_keys)
    elif args.agent:
        simulate_trading(args.agent)
    else:
        # 默认运行DeepSeek
        print("Running DeepSeek Agent by default")
        print("Use --help to see more options\n")
        simulate_trading('deepseek')