# 快速部署指南

## 前置准备

1. **获取 Tushare API Token**
   - 访问 https://tushare.pro/register
   - 注册并登录账号
   - 在个人中心获取 Token

2. **Fork 本项目到你的 GitHub**

## 部署步骤

### 1. 配置 GitHub Secrets

在你的仓库中：

1. 进入 `Settings` > `Secrets and variables` > `Actions`
2. 点击 `New repository secret`
3. 添加：
   - Name: `TUSHARE_API_KEY`
   - Secret: 粘贴你的 Tushare Token
4. 点击 `Add secret`

### 2. 启用 GitHub Pages

1. 进入 `Settings` > `Pages`
2. 在 "Build and deployment" 部分
3. Source 选择: `GitHub Actions`
4. 保存

### 3. 触发首次部署

方法一：推送代码
```bash
git commit --allow-empty -m "Trigger deployment"
git push
```

方法二：手动触发
1. 进入 `Actions` 标签页
2. 选择 "更新A股市场数据" workflow
3. 点击 `Run workflow`
4. 等待完成后，选择 "部署到 GitHub Pages"
5. 再次点击 `Run workflow`

### 4. 访问你的网站

部署成功后，访问：
```
https://你的用户名.github.io/AI-Trader-AShare/
```

## 验证部署

1. **检查数据更新**
   - 进入 Actions 查看 "更新A股市场数据" 是否成功
   - 绿色勾表示成功

2. **检查页面部署**
   - 进入 Actions 查看 "部署到 GitHub Pages" 是否成功
   - 访问网站查看数据是否正常显示

## 常见问题

### Q1: Actions 显示失败
**A:** 检查 Secrets 是否正确配置，Token 是否有效

### Q2: 页面显示但没有数据
**A:**
- 检查 `docs/data/` 目录是否有 JSON 文件
- 手动触发 "更新A股市场数据" workflow

### Q3: Tushare API 调用失败
**A:**
- 确认 Token 有效且未过期
- 检查是否超过调用频率限制（免费版每分钟120次）
- 查看 Actions 日志获取详细错误信息

### Q4: 数据不更新
**A:**
- 检查 workflow 中的 cron 时间是否正确
- GitHub Actions 免费版可能有延迟
- 可以手动触发 workflow 强制更新

## 自定义配置

### 修改更新时间

编辑 `.github/workflows/update-data.yml`:

```yaml
schedule:
  # 每天 UTC 00:00 (北京时间 08:00)
  - cron: '0 0 * * *'

  # 改为每6小时一次
  - cron: '0 */6 * * *'

  # 改为每周一次
  - cron: '0 0 * * 0'
```

### 修改监控股票

编辑 `scripts/fetch_market_data.py`:

```python
# 修改获取的股票数量
top_stocks = fetch_top_stocks(limit=20)  # 改为20只

# 修改历史数据天数
history = fetch_stock_history(stock['ts_code'], days=180)  # 改为180天
```

### 添加更多指数

编辑 `scripts/fetch_market_data.py`:

```python
indices = {
    '000001.SH': '上证指数',
    '399001.SZ': '深证成指',
    '399006.SZ': '创业板指',
    '000300.SH': '沪深300',
    '000016.SH': '上证50',      # 新增
    '000905.SH': '中证500',     # 新增
}
```

## 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/AI-Trader-AShare.git
cd AI-Trader-AShare

# 2. 创建 .env 文件
cp .env.example .env
# 编辑 .env 填入你的 Token

# 3. 安装依赖
uv pip install tushare pandas python-dotenv

# 4. 获取数据
python scripts/fetch_market_data.py

# 5. 本地预览
cd docs
python -m http.server 8000
# 访问 http://localhost:8000
```

## 维护建议

1. **定期检查**
   - 每周检查一次 Actions 是否正常运行
   - 关注 Tushare API 的调用额度

2. **数据备份**
   - GitHub 会自动保存历史数据
   - 建议定期下载备份

3. **更新依赖**
   - 每月检查 Python 包更新
   - 关注 Chart.js 等前端库的更新

## 技术支持

- 提交 Issue: https://github.com/你的用户名/AI-Trader-AShare/issues
- Tushare 文档: https://tushare.pro/document/2
- GitHub Actions 文档: https://docs.github.com/actions
