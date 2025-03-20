
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from config import TOKEN, CHAT_IDS
from news_database import news_collection
from datetime import datetime, timedelta
import asyncio
from lark_bot import send_news_to_lark  # 导入 Lark 发送消息的函数

# 设置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# 启动 机器人 /start 命令
async def start(update: Update, context: CallbackContext):
    # logger.info(f"Received /start command from {update.message.chat_id}")  # 日志输出
    await update.message.reply_text('Hello! I am your Crypto News Bot.')

async def send_latest_news():
    """
    从数据库获取最新的新闻，并推送到 Telegram 频道 和 Lark
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # 查询最近 1 小时的新闻
    all_news = list(news_collection.find({"created_at": {"$gte": one_hour_ago}}).sort("created_at", -1))

    if not all_news:
        print("⚠️ 没有最新新闻，不发送消息")
        logger.info("没有最新新闻，跳过发送")
        return

    message = "📢 **最新交易所（Binance/OKX/Bitget/Bybit/Kucoin/Gate）上币公告** 📢\n\n"
    for news in all_news:
        # message += f"📌 {news['title']}\n🔗 [阅读详情]({news['link']})\n\n"

        # 格式化时间
        # 如果时间包含 "Published on"，则处理这个特殊格式
        # if news["time"].startswith("Published on"):
        #     try:
        #         news_time = datetime.strptime(news["time"][14:], "%b %d, %Y")  # 去掉 "Published on" 前缀并解析
        #         formatted_time = news_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        #     except ValueError:
        #         print(f"❌ 无法解析时间: {news['time']}")
        #         logger.error(f"无法解析时间: {news['time']}")
        #         continue
        # else:
        #     # 解析格式为 'YYYY-MM-DD' 的时间
        #     try:
        #         news_time = datetime.strptime(news["time"], "%Y-%m-%d")
        #         formatted_time = news_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        #     except ValueError:
        #         print(f"❌ 无法解析时间: {news['time']}")
        #         logger.error(f"无法解析时间: {news['time']}")
        #         continue
        
        # 直接使用数据库中已格式化的时间
        formatted_time = news["time"]  # 时间已经是正确的格式
        # 获取来源，如果没有，则使用默认值
        source = news.get('source', 'Unknown Source')

        # 构建消息
        message += f"📌 来自 {source} 的新闻: {news['title']}\n"
        message += f"⏰ 发布时间: {formatted_time}\n"
        message += f"🔗 [阅读详情]({news['link']})\n\n"

    # 发送到 多个Telegram 频道
    try:
        application = Application.builder().token(TOKEN).build()

        async with application:
            for chat_id in CHAT_IDS:  # 遍历每个 chat_id
                await application.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )

        print(f"✅ 成功推送 {len(all_news)} 条新闻")
        logger.info(f"成功推送 {len(all_news)} 条新闻到 Telegram")
    
    except Exception as e:
        print(f"❌ 发送新闻失败: {e}")

    # 发送到 Lark
    send_news_to_lark(message)  # 调用 lark_bot 中的函数将消息发送到 Lark
    print(f"✅ 成功推送 {len(all_news)} 条新闻到 Lark")
    logger.info(f"成功推送 {len(all_news)} 条新闻到 Lark")

# def main():
#     """启动 Telegram 机器人"""
#     # 创建 Application 对象
#     application = Application.builder().
# 
# token(TOKEN).build()
#     # 注册 /start 命令
#     application.add_handler(CommandHandler("start", start))
#     # 启动 Bot
#     application.run_polling()

# if __name__ == '__main__':
#     main()



async def start_bot():
    """
    ✅ 让 Telegram Bot 以异步方式运行，不影响事件循环
    """
    logging.info("✅ Telegram Bot 正在运行...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.start()

    # ✅ **改用 `start()`，而不是 `run_polling()`**
    asyncio.create_task(application.updater.start_polling())

    # ✅ **关键修正：让 `run_polling()` 运行在后台**
    # asyncio.create_task(application.run_polling(allowed_updates=None))

    # ✅ **不阻塞事件循环，避免 `RuntimeError`**
    
    # # ✅ 修正：获取当前运行的事件循环，防止 `run_polling()` 关闭它
    # loop = asyncio.get_running_loop()
    # loop.create_task(application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=True))

# ✅ `if __name__ == '__main__'` 删除，因为 `main.py` 需要调用 `start_bot()`

# 新增的 main 函数，作为入口
async def main():
    await send_latest_news()

if __name__ == '__main__':
    asyncio.run(main())  # 这里调用了 main() 函数