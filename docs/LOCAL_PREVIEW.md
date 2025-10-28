# 本地预览 AI-Trader Dashboard

## 快速启动

### 方法1: 使用Python内置HTTP服务器（推荐）

```bash
# 1. 复制数据到docs目录
python scripts/copy_data_to_docs.py

# 2. 启动HTTP服务器
cd docs
python -m http.server 8000

# 3. 打开浏览器访问
# http://localhost:8000
```

### 方法2: 使用Node.js http-server

```bash
# 1. 安装http-server（首次使用需要安装）
npm install -g http-server

# 2. 复制数据
python scripts/copy_data_to_docs.py

# 3. 启动服务器
cd docs
http-server -p 8000

# 4. 打开浏览器访问
# http://localhost:8000
```

### 方法3: 使用VS Code Live Server插件

1. 安装VS Code Live Server插件
2. 复制数据：`python scripts/copy_data_to_docs.py`
3. 在VS Code中右键 `docs/index.html`
4. 选择 "Open with Live Server"

## 注意事项

1. **数据同步**: 每次运行模拟后，需要执行 `python scripts/copy_data_to_docs.py` 复制最新数据
2. **CORS问题**: 直接双击HTML文件打开会有跨域问题，必须使用HTTP服务器
3. **数据路径**: JavaScript会尝试从以下路径加载数据：
   - `../data/agent_data/` （开发环境）
   - `data/` （生产环境）

## 页面功能

### 左侧面板
- **📈 资产收益曲线**: 显示所有AI模型的收益率走势
- **🏆 AI排行榜**: 根据收益率排名

### 右侧面板
- **💼 交易决策记录**: 显示每笔交易的详细信息
  - 买入/卖出操作
  - 股票代码和名称
  - 价格、数量、金额
  - AI的决策原因

### 交互功能
- 下拉选择框：筛选单个AI模型或查看全部
- 图表可以hover查看具体数值
- 交易记录可以滚动浏览

## 目录结构

```
docs/
├── index.html          # 主页面
├── css/
│   └── style.css       # 样式文件
├── js/
│   └── competition.js  # JavaScript逻辑
└── data/               # 数据文件（需要复制）
    └── DeepSeek_Trader_state.json
```

## 故障排查

### 问题1: 页面显示"暂无数据"

**解决方法:**
1. 确认已运行模拟: `python run_simulation.py`
2. 复制数据到docs: `python scripts/copy_data_to_docs.py`
3. 刷新浏览器页面

### 问题2: 交易记录不显示

**解决方法:**
1. 检查浏览器控制台是否有错误
2. 确认数据文件存在: `docs/data/DeepSeek_Trader_state.json`
3. 检查JSON格式是否正确

### 问题3: 图表不显示

**解决方法:**
1. 检查Chart.js是否加载成功（查看浏览器控制台）
2. 确认数据中有 `daily_snapshots` 字段
3. 清除浏览器缓存后重新加载

## 开发调试

打开浏览器开发者工具（F12），查看Console标签页查看日志：
- 数据加载状态
- 错误信息
- 变量值

## 部署到GitHub Pages

```bash
# 1. 将docs目录推送到GitHub
git add docs/
git commit -m "Update dashboard"
git push

# 2. 在GitHub仓库设置中启用GitHub Pages
# Settings -> Pages -> Source -> docs/ folder

# 3. 访问你的GitHub Pages URL
# https://username.github.io/AI-Trader-AShare/
```
