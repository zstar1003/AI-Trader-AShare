"""
A股价格数据持久化管理
从2024年9月开始记录所有A股的日线数据
"""
import os
import json
import tushare as ts
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv()

# 配置
TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data" / "daily_prices"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 起始日期：2024年9月1日
START_DATE = "20240901"


class PriceDataManager:
    """价格数据管理器"""

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_stock_file_path(self, ts_code: str) -> Path:
        """获取股票数据文件路径"""
        return self.data_dir / f"daily_prices_{ts_code}.json"

    def load_stock_data(self, ts_code: str) -> Dict:
        """加载股票历史数据"""
        file_path = self.get_stock_file_path(ts_code)

        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "Meta Data": {
                    "1. Symbol": ts_code,
                    "2. Last Refreshed": "",
                    "3. Time Zone": "Asia/Shanghai"
                },
                "Time Series (Daily)": {}
            }

    def save_stock_data(self, ts_code: str, data: Dict):
        """保存股票数据"""
        file_path = self.get_stock_file_path(ts_code)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def fetch_and_save_stock_data(self, ts_code: str, start_date: str = START_DATE,
                                   end_date: Optional[str] = None) -> bool:
        """
        从Tushare获取并保存股票数据

        Args:
            ts_code: 股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD，默认为今天

        Returns:
            bool: 是否成功
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')

        try:
            # 获取日线数据
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                print(f"  {ts_code}: 无数据")
                return False

            # 加载现有数据
            stock_data = self.load_stock_data(ts_code)

            # 转换为目标格式
            time_series = stock_data["Time Series (Daily)"]

            for _, row in df.iterrows():
                date_str = row['trade_date']
                # 转换为 YYYY-MM-DD 格式
                date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

                time_series[date_formatted] = {
                    "1. open": f"{float(row['open']):.4f}",
                    "2. high": f"{float(row['high']):.4f}",
                    "3. low": f"{float(row['low']):.4f}",
                    "4. close": f"{float(row['close']):.4f}",
                    "5. volume": str(int(row['vol'] * 100)) if row['vol'] else "0"  # 转换为股数
                }

            # 更新元数据
            stock_data["Meta Data"]["2. Last Refreshed"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 保存数据
            self.save_stock_data(ts_code, stock_data)

            print(f"  {ts_code}: 成功保存 {len(df)} 条记录")
            return True

        except Exception as e:
            print(f"  {ts_code}: 失败 - {e}")
            return False

    def update_stock_data(self, ts_code: str) -> bool:
        """
        更新股票数据（只获取最新的数据）

        Args:
            ts_code: 股票代码

        Returns:
            bool: 是否成功
        """
        # 加载现有数据
        stock_data = self.load_stock_data(ts_code)
        time_series = stock_data["Time Series (Daily)"]

        # 找出最后更新日期
        if time_series:
            dates = list(time_series.keys())
            last_date_str = max(dates)  # YYYY-MM-DD
            # 转换为 YYYYMMDD
            last_date = last_date_str.replace('-', '')
        else:
            last_date = START_DATE

        # 从最后日期的下一天开始更新
        start_date = (datetime.strptime(last_date, '%Y%m%d') + timedelta(days=1)).strftime('%Y%m%d')
        end_date = datetime.now().strftime('%Y%m%d')

        # 如果已是最新，跳过
        if start_date > end_date:
            return True

        return self.fetch_and_save_stock_data(ts_code, start_date, end_date)

    def get_all_stock_list(self) -> List[str]:
        """获取所有A股股票列表"""
        try:
            # 获取所有上市股票
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date'
            )

            stock_list = df['ts_code'].tolist()
            print(f"获取到 {len(stock_list)} 只A股")
            return stock_list

        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []

    def initialize_all_stocks(self, batch_size: int = 50, delay: float = 0.5):
        """
        初始化所有A股的历史数据

        Args:
            batch_size: 每批处理的股票数量
            delay: 每次请求之间的延迟（秒），避免超过API限制
        """
        print("=" * 70)
        print("开始初始化所有A股价格数据")
        print(f"起始日期: {START_DATE}")
        print(f"数据目录: {self.data_dir}")
        print("=" * 70)

        # 获取股票列表
        stock_list = self.get_all_stock_list()
        if not stock_list:
            print("无法获取股票列表")
            return

        total = len(stock_list)
        success_count = 0
        fail_count = 0

        # 分批处理
        for i in range(0, total, batch_size):
            batch = stock_list[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"\n处理第 {batch_num}/{total_batches} 批 ({len(batch)} 只股票)...")

            for ts_code in batch:
                if self.fetch_and_save_stock_data(ts_code):
                    success_count += 1
                else:
                    fail_count += 1

                # 延迟避免超限
                time.sleep(delay)

            print(f"批次完成: 成功 {success_count}, 失败 {fail_count}")

        print("\n" + "=" * 70)
        print(f"初始化完成！")
        print(f"总计: {total} 只股票")
        print(f"成功: {success_count}")
        print(f"失败: {fail_count}")
        print("=" * 70)

    def update_all_stocks(self, batch_size: int = 100, delay: float = 0.3):
        """
        更新所有已存在的股票数据

        Args:
            batch_size: 每批处理的股票数量
            delay: 每次请求之间的延迟（秒）
        """
        print("=" * 70)
        print("开始更新所有A股价格数据")
        print("=" * 70)

        # 获取已存在的数据文件
        existing_files = list(self.data_dir.glob("daily_prices_*.json"))
        total = len(existing_files)

        if total == 0:
            print("未找到任何数据文件，请先运行初始化")
            return

        print(f"找到 {total} 个数据文件")

        success_count = 0
        fail_count = 0
        skip_count = 0

        # 分批处理
        for i in range(0, total, batch_size):
            batch = existing_files[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"\n处理第 {batch_num}/{total_batches} 批 ({len(batch)} 个文件)...")

            for file_path in batch:
                # 从文件名提取股票代码
                filename = file_path.stem  # daily_prices_600000.SH
                ts_code = filename.replace('daily_prices_', '')

                try:
                    if self.update_stock_data(ts_code):
                        success_count += 1
                    else:
                        skip_count += 1
                except Exception as e:
                    print(f"  {ts_code}: 更新失败 - {e}")
                    fail_count += 1

                time.sleep(delay)

            print(f"批次完成: 成功 {success_count}, 跳过 {skip_count}, 失败 {fail_count}")

        print("\n" + "=" * 70)
        print(f"更新完成！")
        print(f"总计: {total} 只股票")
        print(f"成功: {success_count}")
        print(f"跳过: {skip_count}")
        print(f"失败: {fail_count}")
        print("=" * 70)


def main():
    """主函数"""
    import sys

    manager = PriceDataManager()

    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python scripts/price_data_manager.py init     # 初始化所有A股数据")
        print("  python scripts/price_data_manager.py update   # 更新所有A股数据")
        print("  python scripts/price_data_manager.py test     # 测试单只股票")
        return

    command = sys.argv[1]

    if command == "init":
        # 初始化所有股票（从2024年9月开始）
        manager.initialize_all_stocks(batch_size=50, delay=0.5)

    elif command == "update":
        # 更新所有股票数据
        manager.update_all_stocks(batch_size=100, delay=0.3)

    elif command == "test":
        # 测试单只股票
        test_code = "600000.SH"
        print(f"测试获取 {test_code} 的数据...")
        success = manager.fetch_and_save_stock_data(test_code)

        if success:
            # 读取并显示
            data = manager.load_stock_data(test_code)
            time_series = data["Time Series (Daily)"]
            print(f"\n共 {len(time_series)} 条记录")
            print("\n最近5天:")
            for date in sorted(time_series.keys(), reverse=True)[:5]:
                print(f"  {date}: 收盘 {time_series[date]['4. close']}")

    else:
        print(f"未知命令: {command}")


if __name__ == '__main__':
    main()
