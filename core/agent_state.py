"""
Agent状态持久化管理
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class AgentStateManager:
    """Agent状态管理器 - 持久化交易记录和持仓"""

    def __init__(self, agent_name: str, data_dir: Optional[Path] = None):
        self.agent_name = agent_name
        self.data_dir = data_dir or Path(__file__).parent.parent / "data" / "agent_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 状态文件路径
        self.state_file = self.data_dir / f"{agent_name}_state.json"

        # 加载或初始化状态
        self.state = self.load_state()

    def load_state(self) -> Dict:
        """加载Agent状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 初始状态
            return {
                "agent_name": self.agent_name,
                "initial_capital": 1000000.0,  # 初始100万
                "current_capital": 1000000.0,
                "positions": {},  # 持仓 {ts_code: {shares, avg_cost}}
                "trade_history": [],  # 交易历史
                "daily_snapshots": {},  # 每日快照 {date: {capital, total_value}}
                "last_update": "",
                "simulation_start_date": "",
                "simulation_current_date": ""
            }

    def save_state(self):
        """保存Agent状态"""
        self.state["last_update"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def initialize_simulation(self, start_date: str):
        """初始化模拟交易"""
        self.state["simulation_start_date"] = start_date
        self.state["simulation_current_date"] = start_date
        self.state["current_capital"] = self.state["initial_capital"]
        self.state["positions"] = {}
        self.state["trade_history"] = []
        self.state["daily_snapshots"] = {}
        self.save_state()

    def get_current_date(self) -> str:
        """获取当前模拟日期"""
        return self.state["simulation_current_date"]

    def advance_to_date(self, new_date: str):
        """推进到新的交易日"""
        self.state["simulation_current_date"] = new_date
        self.save_state()

    def record_trade(self, trade_info: Dict):
        """记录交易"""
        trade_record = {
            "date": self.state["simulation_current_date"],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            **trade_info
        }
        self.state["trade_history"].append(trade_record)
        self.save_state()

    def update_position(self, ts_code: str, shares: int, avg_cost: float):
        """更新持仓"""
        if shares > 0:
            self.state["positions"][ts_code] = {
                "shares": shares,
                "avg_cost": avg_cost
            }
        else:
            # 清空持仓
            if ts_code in self.state["positions"]:
                del self.state["positions"][ts_code]
        self.save_state()

    def update_capital(self, new_capital: float):
        """更新资金"""
        self.state["current_capital"] = new_capital
        self.save_state()

    def save_daily_snapshot(self, total_value: float, positions_value: float):
        """保存每日快照"""
        date = self.state["simulation_current_date"]
        self.state["daily_snapshots"][date] = {
            "capital": self.state["current_capital"],
            "positions_value": positions_value,
            "total_value": total_value,
            "positions": dict(self.state["positions"])  # 深拷贝持仓
        }
        self.save_state()

    def get_positions(self) -> Dict:
        """获取当前持仓"""
        return self.state["positions"]

    def get_capital(self) -> float:
        """获取当前资金"""
        return self.state["current_capital"]

    def get_trade_history(self) -> List[Dict]:
        """获取交易历史"""
        return self.state["trade_history"]

    def get_daily_snapshots(self) -> Dict:
        """获取每日快照"""
        return self.state["daily_snapshots"]

    def get_summary(self) -> Dict:
        """获取汇总信息"""
        return {
            "agent_name": self.agent_name,
            "initial_capital": self.state["initial_capital"],
            "current_capital": self.state["current_capital"],
            "positions_count": len(self.state["positions"]),
            "trades_count": len(self.state["trade_history"]),
            "simulation_start": self.state["simulation_start_date"],
            "simulation_current": self.state["simulation_current_date"]
        }
