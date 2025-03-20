# Crypto Exchange Listing Bot

一个自动化工具，用于抓取主流加密货币交易所（Binance、OKX、Bitget、Bybit）的上币公告，并通过 Telegram 和飞书（Lark）进行实时推送。

## 功能特点

- 多交易所支持：同时监控 Binance、OKX、Bitget、Bybit、KuCoin 和 Gate.io 的上币公告
- 自动化抓取：使用异步方式并行抓取多个交易所数据
- 数据持久化：使用 MongoDB 进行数据存储和去重
- 多渠道推送：支持 Telegram 和飞书（Lark）双渠道消息推送
- 定时任务：每 30 分钟自动执行一次抓取和推送

## 项目结构

```plaintext
.
├── api_binance_news_scraper.py   # Binance API 抓取实现（备用）
├── bot.py                        # Telegram Bot 核心实现
├── config.py                     # 配置文件（Bot Token、数据库等）
├── config.json                   # 关键词和数据源配置
├── lark_bot.py                  # 飞书机器人实现
├── main.py                      # 主程序入口
├── news_database.py             # MongoDB 数据库操作
├── news_scraper.py              # 新闻抓取核心逻辑
├── task_scheduler.py            # 定时任务调度器
└── test_*.py                    # 测试文件

## 核心模块说明
### 1. 数据抓取模块
- news_scraper.py
  - 实现多交易所并行抓取
  - 支持 Binance、OKX、Bitget、Bybit
### 2. 数据存储模块
- news_database.py
  - MongoDB 数据库操作
  - 自动去重和时间戳记录
### 3. 消息推送模块
- bot.py
  - Telegram Bot 实现
  - 支持多群组推送
- lark_bot.py
  - 飞书机器人实现
  - 支持长消息自动分段
### 4. 任务调度模块
- task_scheduler.py
  - 定时任务管理
  - 30分钟间隔执行

## 配置说明

1. 复制配置文件模板：
```bash
cp config.example.py config.py
cp config.example.json config.json
```
### Telegram 配置
在 config.py 中配置：

- BOT_TOKEN：Telegram Bot 的访问令牌
- CHAT_IDS：需要推送消息的群组 ID 列表

### 飞书配置
在 config.py 中配置：

- LARK_WEBHOOK_URL：飞书机器人的 Webhook 地址

### 数据库配置
在 config.py 中配置：
- MONGO_URI：MongoDB 连接地址

## 运行说明
1. 安装依赖
```bash
pip install -r requirements.txt
 ```

2. 启动 MongoDB
```bash
mongod --dbpath ./data/db
 ```

3. 运行程序
```bash
python main.py
 ```

## 主要功能流程
1. 定时任务触发（每 30 分钟）
2. 并行抓取各交易所公告
3. 数据存储并去重
4. 推送新消息到 Telegram 和飞书

## 开发说明
- Python 3.7+
- 异步编程（asyncio）
- MongoDB 数据库
- Telegram Bot API
- 飞书自定义机器人

## 注意事项
1. 确保 MongoDB 服务正常运行
2. 配置文件中的 Telegram Bot Token 和 Lark Webhook Token 需要自行申请
3. 推送频道的 ID 需要提前获取
4. 建议使用 Python 3.7+

## 维护者
[维护者信息]

## 许可证
MIT License


## 快速开始

1. 克隆仓库
```bash
git clone https://github.com/xifengxx/tg-crypto-bot.git
cd tg-crypto-bot
```

## 贡献指南
1. Fork 本仓库
2. 创建你的特性分支 ( git checkout -b feature/AmazingFeature )
3. 提交你的改动 ( git commit -m 'Add some AmazingFeature' )
4. 推送到分支 ( git push origin feature/AmazingFeature )
5. 提交 Pull Request

## 问题反馈
如果你有任何问题或建议，欢迎在 Issues 中提出。

## Star History
如果这个项目对你有帮助，欢迎点个 star ⭐️