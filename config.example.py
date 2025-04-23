# config.example.py
import os

# 优先从环境变量获取配置，如果没有则使用默认值
# Telegram Bot Token
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'your_telegram_bot_token')

# 发送消息的多个 Telegram 群组的 chat_id 列表
CHAT_IDS_STR = os.environ.get('TELEGRAM_CHAT_IDS', 'chat_id_1,chat_id_2')
CHAT_IDS = CHAT_IDS_STR.split(',')

# MongoDB连接字符串
# 优先使用环境变量中的 MongoDB URI，如果没有则使用本地的
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')

# Lark机器人
LARK_WEBHOOK_URL = os.environ.get('LARK_WEBHOOK_URL', 'your_lark_webhook_url')

# 运行环境标识
IS_PRODUCTION = os.environ.get('RAILWAY_ENVIRONMENT', 'local') != 'local'