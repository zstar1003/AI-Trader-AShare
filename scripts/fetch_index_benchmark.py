"""
获取上证指数基准数据
用于对比AI交易表现
"""
import os
import json
import tushare as ts
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# 初始化Tushare
TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()

def get_index_data(start_date='20251015', end_date='20251027'):
    """
    获取上证指数数据

    Args:
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    print(f"Fetching Shanghai Composite Index data: {start_date} - {end_date}")

    # 获取上证指数数据 (000001.SH)
    df = pro.index_daily(ts_code='000001.SH', start_date=start_date, end_date=end_date)

    if df.empty:
        print("No data found!")
        return None

    # 按日期排序
    df = df.sort_values('trade_date')

    # 计算收益率
    first_close = df.iloc[0]['close']
    benchmark_data = {
        'name': 'Shanghai Composite Index',
        'ts_code': '000001.SH',
        'start_date': start_date,
        'end_date': end_date,
        'base_value': float(first_close),
        'daily_data': []
    }

    for _, row in df.iterrows():
        daily_return = ((row['close'] - first_close) / first_close) * 100
        benchmark_data['daily_data'].append({
            'date': row['trade_date'],
            'close': float(row['close']),
            'return_pct': float(daily_return)
        })

    return benchmark_data

def save_index_data():
    """保存上证指数数据"""
    # 获取数据
    index_data = get_index_data()

    if not index_data:
        print("Failed to fetch index data")
        return

    # 保存到data目录
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    output_file = data_dir / "index_benchmark.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Index benchmark data saved to: {output_file}")
    print(f"  Date range: {index_data['start_date']} - {index_data['end_date']}")
    print(f"  Days: {len(index_data['daily_data'])}")
    print(f"  Base value: {index_data['base_value']:.2f}")
    print(f"  Final return: {index_data['daily_data'][-1]['return_pct']:.2f}%")

    # 同时保存到docs目录
    docs_dir = Path(__file__).parent.parent / "docs" / "data"
    docs_dir.mkdir(parents=True, exist_ok=True)
    docs_file = docs_dir / "index_benchmark.json"

    with open(docs_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Also copied to: {docs_file}")

if __name__ == "__main__":
    save_index_data()
