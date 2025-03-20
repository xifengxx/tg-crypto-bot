

import asyncio
from telegram import Bot

BOT_TOKEN = "8171650721:AAFxtapeLKemusUJAkWHLZEzGssZ5VUeFfI"  # 替换为你的 Bot Token

async def get_chat_id():
    bot = Bot(token=BOT_TOKEN)
    updates = await bot.get_updates()  # 使用 await 等待异步调用完成

    for update in updates:
        chat_id = update.message.chat.id if update.message else "No Chat ID"
        message_text = update.message.text if update.message else "No Message"
        print(f"Chat ID: {chat_id}")  # 打印聊天 ID
        print(f"Message: {message_text}")  # 打印消息内容

if __name__ == "__main__":
    asyncio.run(get_chat_id())  # 使用 asyncio 运行异步函数