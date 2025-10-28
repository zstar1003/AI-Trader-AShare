"""
AI交易竞赛主程序 - 重构版
使用LangChain Agent和Tools系统
"""
import json
import os
import tushare as ts
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

from core import TradingEngine, MarketDataProvider
from tools import TradingTools
from agents import BaseTradingAgent, DeepSeekAgent

load_dotenv()

# 配置Tushare
TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()


class TradingCompetition:
    """交易竞赛管理器"""

    def __init__(self, initial_cash: float = 1000000, trading_days: int = 10):
        self.initial_cash = initial_cash
        self.trading_days = trading_days
        self.agents: List[BaseTradingAgent] = []
        self.engines: Dict[str, TradingEngine] = {}
        self.competition_results = {}

    def register_agent(self, agent: BaseTradingAgent):
        """注册参赛Agent"""
        self.agents.append(agent)
        self.engines[agent.name] = TradingEngine(initial_cash=self.initial_cash)
        print(f"注册Agent: {agent.name} ({agent.model_name})")

    def run_competition(self, output_dir: str = "docs/data"):
        """运行竞赛"""
        print("\n" + "=" * 70)
        print("AI交易竞赛开始")
        print("=" * 70)
        print(f"初始资金: ¥{self.initial_cash:,.2f}")
        print(f"交易天数: {self.trading_days}天")
        print(f"参赛Agent: {len(self.agents)}个")
        print("=" * 70)

        # 获取交易日列表
        trading_dates = MarketDataProvider.get_recent_trading_dates(pro, self.trading_days)
        if not trading_dates:
            print("无法获取交易日数据")
            return

        print(f"\n交易周期: {trading_dates[0]} - {trading_dates[-1]}")

        # 获取可交易股票列表
        stock_pool = MarketDataProvider.get_stock_list(pro, limit=50)
        if not stock_pool:
            print("无法获取股票列表")
            return

        print(f"股票池: {len(stock_pool)}只股票")

        # 逐日模拟交易
        for day_idx, trade_date in enumerate(trading_dates, 1):
            print(f"\n{'='*70}")
            print(f"交易日 {day_idx}/{len(trading_dates)}: {trade_date}")
            print(f"{'='*70}")

            # 获取当日股票价格
            stocks_with_price = self._get_stocks_with_price(stock_pool, trade_date)
            if not stocks_with_price:
                print(f"  跳过(无价格数据)")
                continue

            # 每个Agent进行决策和交易
            for agent in self.agents:
                print(f"\n[{agent.name}] 开始决策...")
                self._process_agent_trading(
                    agent=agent,
                    engine=self.engines[agent.name],
                    trade_date=trade_date,
                    stocks_with_price=stocks_with_price
                )

            # 更新所有Agent的持仓价格和记录每日资产
            self._update_daily_values(trade_date, stocks_with_price)

        # 生成竞赛报告
        self._generate_report(trading_dates, output_dir)

    def _get_stocks_with_price(self, stock_pool: List[Dict], trade_date: str) -> List[Dict]:
        """获取带价格的股票列表"""
        stocks_with_price = []

        for stock in stock_pool:
            price_data = MarketDataProvider.get_stock_price(pro, stock['ts_code'], trade_date)
            if price_data:
                stock_info = stock.copy()
                stock_info.update(price_data)
                stocks_with_price.append(stock_info)

        return stocks_with_price

    def _process_agent_trading(self, agent: BaseTradingAgent, engine: TradingEngine,
                                trade_date: str, stocks_with_price: List[Dict]):
        """处理Agent的交易"""
        # 更新持仓价格
        price_map = {s['ts_code']: s['close'] for s in stocks_with_price}
        engine.update_positions_price(trade_date, price_map)

        # 创建交易工具
        trading_tools = TradingTools(
            engine=engine,
            market_data_provider=None,
            current_date=trade_date,
            available_stocks=stocks_with_price
        )
        tools = trading_tools.get_tools()

        # 初始化Agent（如果还没有）
        if not agent.agent_executor:
            agent.create_agent(tools)

        # 构建上下文
        context = self._build_context(engine, stocks_with_price, trade_date)

        # Agent做出决策并执行
        try:
            result = agent.make_decision(context)
            print(f"[{agent.name}] 决策完成")
            # print(f"结果: {result[:200]}...")  # 打印部分结果
        except Exception as e:
            print(f"[{agent.name}] 决策失败: {e}")

    def _build_context(self, engine: TradingEngine, stocks_with_price: List[Dict],
                      trade_date: str) -> str:
        """构建市场上下文"""
        summary = engine.get_portfolio_summary()

        context = f"""交易日期: {trade_date}

请分析当前投资组合状态和市场情况，做出交易决策。

注意事项：
1. 可以通过工具查看详细的投资组合状态、可交易股票列表、股票价格
2. 买入时股数必须是100的倍数
3. 建议分散投资，单只股票不超过总资产30%
4. 当前总资产: ¥{summary['total_assets']:,.2f}
5. 可用现金: ¥{summary['cash']:,.2f}

请使用工具进行分析和交易决策。"""

        return context

    def _update_daily_values(self, trade_date: str, stocks_with_price: List[Dict]):
        """更新每日资产价值"""
        price_map = {s['ts_code']: s['close'] for s in stocks_with_price}

        for agent_name, engine in self.engines.items():
            engine.update_positions_price(trade_date, price_map)
            engine.record_daily_value(trade_date)

    def _generate_report(self, trading_dates: List[str], output_dir: str):
        """生成竞赛报告"""
        print("\n" + "=" * 70)
        print("竞赛结果")
        print("=" * 70)

        results = []

        for agent in self.agents:
            engine = self.engines[agent.name]
            summary = engine.get_portfolio_summary()
            result = engine.export_results()

            result['agent_name'] = agent.name
            result['model_name'] = agent.model_name

            results.append({
                'name': agent.name,
                'model': agent.model_name,
                'final_assets': summary['total_assets'],
                'return_pct': summary['total_return_pct'],
                'trades_count': summary['trades_count']
            })

            print(f"\n{agent.name} ({agent.model_name}):")
            print(f"  最终资产: ¥{summary['total_assets']:,.2f}")
            print(f"  总收益率: {summary['total_return_pct']:+.2f}%")
            print(f"  交易次数: {summary['trades_count']}")

        # 按收益率排序
        results.sort(key=lambda x: x['return_pct'], reverse=True)

        print(f"\n{'='*70}")
        print("排名:")
        print(f"{'='*70}")
        for rank, result in enumerate(results, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f" {rank}."
            print(f"{medal} {result['name']:20s} | 收益率: {result['return_pct']:+8.2f}% | "
                  f"资产: ¥{result['final_assets']:,.2f}")

        # 保存结果
        os.makedirs(output_dir, exist_ok=True)

        # 保存竞赛摘要
        competition_summary = {
            'start_date': trading_dates[0],
            'end_date': trading_dates[-1],
            'trading_days': len(trading_dates),
            'initial_cash': self.initial_cash,
            'agents_count': len(self.agents),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'rankings': results
        }

        with open(os.path.join(output_dir, 'competition_summary.json'), 'w', encoding='utf-8') as f:
            json.dump(competition_summary, f, ensure_ascii=False, indent=2)

        # 保存每个Agent的详细结果
        for agent in self.agents:
            engine = self.engines[agent.name]
            result = engine.export_results()
            result['agent_name'] = agent.name
            result['model_name'] = agent.model_name

            filename = f"agent_{agent.name.replace(' ', '_').lower()}.json"
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {output_dir}")
        print("=" * 70)


def main():
    """主函数"""
    # 创建竞赛
    competition = TradingCompetition(
        initial_cash=1000000,  # 100万初始资金
        trading_days=10  # 最近10个交易日
    )

    # 注册参赛Agent
    try:
        competition.register_agent(DeepSeekAgent())
    except Exception as e:
        print(f"注册DeepSeek Agent失败: {e}")

    # 可选：注册更多Agent
    # try:
    #     competition.register_agent(GPT4Agent())
    # except Exception as e:
    #     print(f"注册GPT-4 Agent失败: {e}")

    # try:
    #     competition.register_agent(ClaudeAgent())
    # except Exception as e:
    #     print(f"注册Claude Agent失败: {e}")

    if len(competition.agents) == 0:
        print("错误: 没有成功注册任何Agent")
        return

    # 运行竞赛
    competition.run_competition()


if __name__ == '__main__':
    main()
