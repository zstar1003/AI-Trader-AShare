"""
AI交易竞赛主程序
运行多个AI Agent进行模拟交易比赛
"""
import json
import os
from datetime import datetime
from typing import List, Dict
from trading_engine import TradingEngine, MarketDataProvider
from trading_agents import (
    BaseTradingAgent, DeepSeekAgent, GPT4Agent, ClaudeAgent, RandomAgent,
    MarketContext, TradingDecision
)


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
        trading_dates = MarketDataProvider.get_recent_trading_dates(self.trading_days)
        if not trading_dates:
            print("无法获取交易日数据")
            return

        print(f"\n交易周期: {trading_dates[0]} - {trading_dates[-1]}")

        # 获取可交易股票列表
        stock_pool = MarketDataProvider.get_stock_list(limit=50)
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
            price_data = MarketDataProvider.get_stock_price(stock['ts_code'], trade_date)
            if price_data:
                stock_info = stock.copy()
                stock_info.update(price_data)
                stocks_with_price.append(stock_info)

        return stocks_with_price

    def _process_agent_trading(self, agent: BaseTradingAgent, engine: TradingEngine,
                                trade_date: str, stocks_with_price: List[Dict]):
        """处理Agent的交易"""
        # 准备市场上下文
        context = MarketContext(
            date=trade_date,
            available_stocks=stocks_with_price,
            current_portfolio=self._get_portfolio_info(engine, stocks_with_price),
            market_data={}
        )

        # Agent做出决策
        decision = agent.make_decision(context)

        # 执行交易
        self._execute_decision(agent, engine, trade_date, decision, stocks_with_price)

    def _get_portfolio_info(self, engine: TradingEngine,
                            stocks_with_price: List[Dict]) -> Dict:
        """获取投资组合信息"""
        # 更新持仓价格
        price_map = {s['ts_code']: s['close'] for s in stocks_with_price}
        engine.update_positions_price("", price_map)

        # 获取摘要
        summary = engine.get_portfolio_summary()

        # 添加详细持仓信息
        positions = []
        for ts_code, pos in engine.portfolio.positions.items():
            positions.append({
                'ts_code': pos.ts_code,
                'name': pos.name,
                'shares': pos.shares,
                'avg_price': pos.avg_price,
                'current_price': pos.current_price,
                'market_value': pos.market_value,
                'profit_loss': pos.profit_loss,
                'profit_loss_pct': pos.profit_loss_pct
            })

        summary['positions'] = positions
        return summary

    def _execute_decision(self, agent: BaseTradingAgent, engine: TradingEngine,
                          trade_date: str, decision: TradingDecision,
                          stocks_with_price: List[Dict]):
        """执行交易决策"""
        action_str = f"  [{agent.name}] "

        if decision.action == 'buy' and decision.ts_code and decision.shares:
            # 查找股票信息
            stock = next((s for s in stocks_with_price if s['ts_code'] == decision.ts_code), None)
            if stock:
                success = engine.buy(
                    date=trade_date,
                    ts_code=decision.ts_code,
                    name=stock['name'],
                    price=stock['close'],
                    shares=decision.shares,
                    reason=decision.reason
                )

                if success:
                    action_str += f"买入 {stock['name']} {decision.shares}股 @ ¥{stock['close']:.2f}"
                    print(action_str)
                    print(f"       理由: {decision.reason[:60]}...")
                else:
                    print(action_str + "买入失败")

        elif decision.action == 'sell' and decision.ts_code and decision.shares:
            # 查找持仓
            if decision.ts_code in engine.portfolio.positions:
                pos = engine.portfolio.positions[decision.ts_code]
                stock = next((s for s in stocks_with_price if s['ts_code'] == decision.ts_code), None)

                if stock:
                    success = engine.sell(
                        date=trade_date,
                        ts_code=decision.ts_code,
                        name=stock['name'],
                        price=stock['close'],
                        shares=min(decision.shares, pos.shares),
                        reason=decision.reason
                    )

                    if success:
                        action_str += f"卖出 {stock['name']} {decision.shares}股 @ ¥{stock['close']:.2f}"
                        print(action_str)
                        print(f"       理由: {decision.reason[:60]}...")
                    else:
                        print(action_str + "卖出失败")

        else:
            # 持有
            print(action_str + "持有")

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
    competition.register_agent(DeepSeekAgent())
    competition.register_agent(RandomAgent())  # 基准Agent

    # 可选：注册更多Agent
    # competition.register_agent(GPT4Agent())
    # competition.register_agent(ClaudeAgent())

    # 运行竞赛
    competition.run_competition()


if __name__ == '__main__':
    main()
