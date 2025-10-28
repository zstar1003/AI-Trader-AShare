# 价格数据持久化

## 目录结构

```
data/
└── daily_prices/
    ├── daily_prices_600000.SH.json
    ├── daily_prices_600036.SH.json
    └── ...
```

## 数据格式

每只股票一个JSON文件，格式如下：

```json
{
    "Meta Data": {
        "1. Symbol": "600000.SH",
        "2. Last Refreshed": "2025-01-28 11:14:57",
        "3. Time Zone": "Asia/Shanghai"
    },
    "Time Series (Daily)": {
        "2025-01-08": {
            "1. open": "10.2600",
            "2. high": "10.3700",
            "3. low": "10.1800",
            "4. close": "10.2600",
            "5. volume": "48237450"
        },
        "2025-01-07": {
            "1. open": "10.2400",
            "2. high": "10.3200",
            "3. low": "10.1500",
            "4. close": "10.2300",
            "5. volume": "52341234"
        }
    }
}
```

## 使用方法

### 1. 测试单只股票

```bash
python scripts/price_data_manager.py test
```

### 2. 初始化所有A股数据（从2024年9月开始）

**注意**: 全量初始化约5000只股票，需要较长时间（约2-3小时）

```bash
# 方式1：一次性运行（不推荐）
python scripts/price_data_manager.py init

# 方式2：分批运行（推荐）
# 第一次运行会初始化前50只，然后可以多次运行
# 脚本会自动跳过已存在的文件
python scripts/price_data_manager.py init
```

参数说明：
- `batch_size=50`: 每批处理50只股票
- `delay=0.5`: 每次API调用间隔0.5秒（避免超限）

### 3. 更新所有已存在的股票数据

```bash
# 更新所有已下载的股票数据到最新
python scripts/price_data_manager.py update
```

### 4. 在Python代码中使用

```python
from core.market_data import MarketDataProvider
import tushare as ts
from pathlib import Path

# 初始化
pro = ts.pro_api()
data_provider = MarketDataProvider(pro)

# 从JSON获取价格
price = data_provider.get_stock_price_from_json('600000.SH', '20250108')

# 混合模式（优先JSON，失败则API）
price = data_provider.get_stock_price_hybrid('600000.SH', '20250108')

# 获取所有已有数据的股票
all_stocks = data_provider.get_all_stocks_from_json()
print(f"已有 {len(all_stocks)} 只股票的数据")
```

## GitHub Actions 自动更新

在 `.github/workflows/update-prices.yml`:

```yaml
name: 更新价格数据

on:
  schedule:
    - cron: '0 16 * * *'  # 每天北京时间00:00更新
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: 安装依赖
        run: pip install tushare pandas python-dotenv
      - name: 更新数据
        env:
          TUSHARE_API_KEY: ${{ secrets.TUSHARE_API_KEY }}
        run: python scripts/price_data_manager.py update
      - name: 提交更新
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/daily_prices/*.json
          git commit -m "更新价格数据 $(date +'%Y-%m-%d')" || exit 0
          git push
```

## 数据特点

- **时间范围**: 从2024年9月1日开始
- **更新频率**: 每日收盘后更新
- **数据量**: 每只股票约60KB（~300个交易日）
- **总数据量**: 约5000只 × 60KB = 300MB

## 注意事项

1. **API限制**: Tushare免费用户每分钟120次调用，脚本已设置延迟避免超限
2. **磁盘空间**: 确保有至少500MB可用空间
3. **初始化时间**: 全量初始化需要2-3小时
4. **Git LFS**: 如果数据文件过大，考虑使用Git LFS

## 性能优化建议

1. **增量更新**: 使用 `update` 命令只更新新数据
2. **并行处理**: 可以修改脚本使用多线程（注意API限制）
3. **压缩存储**: 考虑使用gzip压缩JSON文件

## 故障排除

### 问题1: API调用失败
```
解决: 检查TUSHARE_API_KEY是否正确，是否超过调用限制
```

### 问题2: 数据文件损坏
```
解决: 删除对应的JSON文件，重新运行初始化
```

### 问题3: 磁盘空间不足
```
解决: 清理旧数据或扩展磁盘空间
```
