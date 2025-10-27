"""
A股市场数据获取脚本
使用Tushare API获取市场数据并保存为JSON格式
"""
import tushare as ts
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

TUSHARE_API_KEY = os.getenv("TUSHARE_API_KEY")
ts.set_token(TUSHARE_API_KEY)
pro = ts.pro_api()

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_date_range(days=365):
    """获取日期范围"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')

def fetch_index_daily(ts_code='000001.SH', days=365):
    """
    获取指数日线数据
    ts_code: 指数代码
        - 000001.SH: 上证指数
        - 399001.SZ: 深证成指
        - 399006.SZ: 创业板指
        - 000300.SH: 沪深300
    """
    start_date, end_date = get_date_range(days)

    try:
        df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        df = df.sort_values('trade_date')

        # 转换为前端需要的格式
        data = []
        for _, row in df.iterrows():
            data.append({
                'date': row['trade_date'],
                'close': float(row['close']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row['vol']),
                'change': float(row['pct_chg']) if pd.notna(row['pct_chg']) else 0
            })

        return data
    except Exception as e:
        print(f"获取指数数据失败: {e}")
        return []

def fetch_top_stocks(limit=10):
    """获取市值前N的股票"""
    try:
        # 获取今日交易日期
        today = datetime.now().strftime('%Y%m%d')

        # 获取股票基本信息
        df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,list_date')

        # 获取最新市值数据
        df_market = pro.daily_basic(trade_date=today, fields='ts_code,total_mv,circ_mv,pe_ttm,pb,ps_ttm')

        if df_market.empty:
            # 如果今天没有数据，尝试获取前一个交易日
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            df_market = pro.daily_basic(trade_date=yesterday, fields='ts_code,total_mv,circ_mv,pe_ttm,pb,ps_ttm')

        # 合并数据
        df = df.merge(df_market, on='ts_code', how='inner')

        # 按总市值排序
        df = df.sort_values('total_mv', ascending=False).head(limit)

        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                'ts_code': row['ts_code'],
                'name': row['name'],
                'industry': row['industry'] if pd.notna(row['industry']) else '未知',
                'market_value': float(row['total_mv']) if pd.notna(row['total_mv']) else 0,
                'pe_ttm': float(row['pe_ttm']) if pd.notna(row['pe_ttm']) else 0,
                'pb': float(row['pb']) if pd.notna(row['pb']) else 0
            })

        return stocks
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return []

def fetch_stock_history(ts_code, days=365):
    """获取股票历史数据"""
    start_date, end_date = get_date_range(days)

    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        df = df.sort_values('trade_date')

        data = []
        for _, row in df.iterrows():
            data.append({
                'date': row['trade_date'],
                'close': float(row['close']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'volume': float(row['vol']) if pd.notna(row['vol']) else 0,
                'change': float(row['pct_chg']) if pd.notna(row['pct_chg']) else 0
            })

        return data
    except Exception as e:
        print(f"获取股票历史数据失败 {ts_code}: {e}")
        return []

def calculate_performance_metrics(data):
    """计算性能指标"""
    if not data:
        return {}

    prices = [d['close'] for d in data]

    if len(prices) < 2:
        return {}

    total_return = ((prices[-1] - prices[0]) / prices[0]) * 100

    # 计算最大回撤
    peak = prices[0]
    max_drawdown = 0
    for price in prices:
        if price > peak:
            peak = price
        drawdown = ((peak - price) / peak) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    return {
        'total_return': round(total_return, 2),
        'max_drawdown': round(max_drawdown, 2),
        'start_value': round(prices[0], 2),
        'end_value': round(prices[-1], 2)
    }

def main():
    """主函数"""
    print("开始获取A股市场数据...")

    # 1. 获取主要指数数据
    indices = {
        '000001.SH': '上证指数',
        '399001.SZ': '深证成指',
        '399006.SZ': '创业板指',
        '000300.SH': '沪深300'
    }

    index_data = {}
    for code, name in indices.items():
        print(f"获取 {name} 数据...")
        data = fetch_index_daily(code, days=365)
        if data:
            metrics = calculate_performance_metrics(data)
            index_data[code] = {
                'name': name,
                'code': code,
                'data': data,
                'metrics': metrics
            }

    # 保存指数数据
    with open(os.path.join(OUTPUT_DIR, 'indices.json'), 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    print(f"指数数据已保存")

    # 2. 获取热门股票
    print("获取热门股票列表...")
    top_stocks = fetch_top_stocks(limit=20)

    # 3. 获取每只股票的历史数据
    stocks_data = {}
    for stock in top_stocks[:10]:  # 只获取前10只的详细数据
        print(f"获取 {stock['name']} 历史数据...")
        history = fetch_stock_history(stock['ts_code'], days=365)
        if history:
            metrics = calculate_performance_metrics(history)
            stocks_data[stock['ts_code']] = {
                'name': stock['name'],
                'code': stock['ts_code'],
                'industry': stock['industry'],
                'market_value': stock['market_value'],
                'data': history,
                'metrics': metrics
            }

    # 保存股票数据
    with open(os.path.join(OUTPUT_DIR, 'stocks.json'), 'w', encoding='utf-8') as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
    print(f"股票数据已保存")

    # 4. 生成汇总信息
    summary = {
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'indices_count': len(index_data),
        'stocks_count': len(stocks_data),
        'trading_period': f"{get_date_range(365)[0]} - {get_date_range(365)[1]}"
    }

    with open(os.path.join(OUTPUT_DIR, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"汇总信息已保存")

    print("\n数据获取完成!")
    print(f"- 指数数量: {len(index_data)}")
    print(f"- 股票数量: {len(stocks_data)}")
    print(f"- 数据保存路径: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
