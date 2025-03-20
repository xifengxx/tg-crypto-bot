# config.example.py

# Telegram Bot Token
TOKEN = 'your_telegram_bot_token'

# 发送消息的多个 Telegram 群组的 chat_id 列表
CHAT_IDS = [
    'your_chat_id_1',  # 群组 1 的 chat_id
    'your_chat_id_2'   # 群组 2 的 chat_id
]

# MongoDB连接字符串
MONGO_URI = 'mongodb://localhost:27017'  # 如果你使用本地的 MongoDB 服务
# 或者你使用 MongoDB Atlas 等云服务的连接字符串
# MONGO_URI = "mongodb+srv://<username>:<password>@cluster.mongodb.net/test"

# Lark机器人
LARK_WEBHOOK_URL = 'your_lark_webhook_url'