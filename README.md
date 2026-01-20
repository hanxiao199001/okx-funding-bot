# OKX资金费率套利交易系统

🤖 自动化加密货币资金费率套利策略

## 功能

- 📊 实时数据采集（每5分钟）
- 🎯 自动信号检测
- 💼 纸面交易模拟
- 🎛️ 实时监控仪表盘

## 快速开始

\`\`\`bash
# 1. 安装依赖
pip install requests pandas schedule

# 2. 启动数据采集
python okx_crawler.py

# 3. 启动纸面交易
python paper_bot.py loop

# 4. 查看仪表盘
python dashboard.py
\`\`\`

## 策略说明

- 做空信号：资金费率 > 0.5%
- 做多信号：资金费率 < -0.3%
- 止盈：+1.5%
- 止损：-2%

## 文件说明

- `okx_crawler.py` - 数据采集爬虫
- `paper_bot.py` - 纸面交易机器人
- `dashboard.py` - 监控仪表盘
- `monitor_signals.py` - 实时信号监控
- `funding_strategy.py` - 策略回测

## 注意

⚠️ 仅供学习研究，实盘交易风险自负
