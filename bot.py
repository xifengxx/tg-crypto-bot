
# bot.py
import logging
import os
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from datetime import datetime, timedelta
import asyncio

# 在文件顶部的日志设置部分
# 设置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# 降低 httpx 和 telegram 模块的日志级别
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

# 尝试从 config 导入 TOKEN 和 CHAT_IDS，如果失败则使用环境变量
try:
    from config import TOKEN, CHAT_IDS
    logger.info("成功从 config.py 导入 TOKEN 和 CHAT_IDS")
except ImportError:
    logger.warning("无法导入 config 模块，将使用环境变量")
    # 从环境变量获取 TOKEN 和 CHAT_IDS
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    CHAT_IDS_STR = os.environ.get('TELEGRAM_CHAT_IDS', '')
    CHAT_IDS = CHAT_IDS_STR.split(',') if CHAT_IDS_STR else []
    logger.info(f"使用环境变量中的 TOKEN 和 CHAT_IDS: {CHAT_IDS}")

# 尝试导入 news_collection 和 lark_bot
try:
    from news_database import news_collection
except ImportError as e:
    logger.error(f"导入 news_database 模块失败: {e}")
    # 创建一个备用的集合
    class FallbackCollection:
        def __init__(self):
            self.data = []
        def find(self, query=None):
            return self.data
    news_collection = FallbackCollection()

try:
    from lark_bot import send_news_to_lark
except ImportError as e:
    logger.error(f"导入 lark_bot 模块失败: {e}")
    # 创建一个备用的发送函数
    def send_news_to_lark(message):
        logger.warning(f"Lark 发送消息失败，无法导入 lark_bot 模块")

# 启动 机器人 /start 命令
async def start(update: Update, context: CallbackContext):
    # logger.info(f"Received /start command from {update.message.chat_id}")  # 日志输出
    await update.message.reply_text('Hello! I am your Crypto News Bot.')

# 修改 send_latest_news 函数中的 MongoDB 查询
# 修改 send_latest_news 函数，添加消息分割功能
async def send_latest_news():
    """
    从数据库获取最新的新闻，并推送到 Telegram 频道 和 Lark
    """
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # 查询最近 1 小时的新闻
    try:
        # 正确使用 sort 方法，使用关键字参数
        all_news = list(news_collection.find({"created_at": {"$gte": one_hour_ago}}).sort("created_at", -1))
    except TypeError:
        # 备用方法，适用于 FallbackCollection
        logger.warning("使用备用方法获取新闻")
        all_news = list(news_collection.find({"created_at": {"$gte": one_hour_ago}}))

    if not all_news:
        print("⚠️ 没有最新新闻，不发送消息")
        logger.info("没有最新新闻，跳过发送")
        return

    # 构建消息
    message_header = f"🔔 最新加密货币新闻 ({len(all_news)}条):\n\n"
    
    # 添加每条新闻
    news_items = []
    for news in all_news:
        news_text = f"📌 {news.get('title', '无标题')}\n"
        news_text += f"🔗 {news.get('link', '#')}\n"
        news_text += f"📅 {news.get('time', '未知时间')}\n"
        news_text += f"📰 来源: {news.get('source', '未知来源')}\n\n"
        news_items.append(news_text)
    
    # 发送到 Telegram
    try:
        # 分割消息，每条消息最多不超过 4000 字符（留出一些余量）
        telegram_messages = []
        current_message = message_header
        
        for item in news_items:
            # 如果添加这条新闻后消息长度超过 4000 字符，则创建新消息
            if len(current_message) + len(item) > 4000:
                telegram_messages.append(current_message)
                current_message = f"🔔 最新加密货币新闻 (续):\n\n{item}"
            else:
                current_message += item
        
        # 添加最后一条消息
        if current_message:
            telegram_messages.append(current_message)
        
        # 发送所有消息
        for chat_id in CHAT_IDS:
            for msg in telegram_messages:
                await application.bot.send_message(chat_id=chat_id, text=msg, disable_web_page_preview=True)
        
        print(f"✅ 成功推送 {len(all_news)} 条新闻到 Telegram，共 {len(telegram_messages)} 条消息")
    except Exception as e:
        print(f"❌ 发送新闻失败: {e}")
    
    # 发送到 Lark
    try:
        # 构建 Lark 消息
        lark_message = f"🔔 最新加密货币新闻 ({len(all_news)}条):\n\n"
        for news in all_news:
            lark_message += f"📌 {news.get('title', '无标题')}\n"
            lark_message += f"🔗 {news.get('link', '#')}\n"
            lark_message += f"📅 {news.get('time', '未知时间')}\n"
            lark_message += f"📰 来源: {news.get('source', '未知来源')}\n\n"
        
        # 发送到 Lark
        send_news_to_lark(lark_message)
        print(f"✅ 成功推送 {len(all_news)} 条新闻到 Lark")
    except Exception as e:
        print(f"❌ 发送到 Lark 失败: {e}")

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
    让 Telegram Bot 以异步方式运行，不影响事件循环
    """
    global application  # 确保使用全局变量
    
    # 检查运行环境
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    environment_name = "Railway环境" if is_railway else "本地环境"
    logging.info(f"🌍 当前在【{environment_name}】中启动 Telegram Bot")
    logging.info("✅ Telegram Bot 正在运行...")
    
    # 创建应用实例
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # 先尝试删除任何现有的webhook，确保不会有冲突
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("成功删除现有webhook")
    except Exception as e:
        logger.error(f"删除webhook时出错: {e}")
    
    # 初始化应用
    await application.initialize()
    
    # 启动应用但不阻塞
    await application.start()
    
    # 创建轮询任务，但设置较长的超时时间，减少请求频率
    polling_task = asyncio.create_task(
        application.updater.start_polling(
            poll_interval=10.0,  # 增加轮询间隔到10秒
            timeout=30,          # 增加超时时间
            drop_pending_updates=True,  # 丢弃挂起的更新，避免处理旧消息
            allowed_updates=Update.ALL_TYPES
        )
    )
    
    # 返回轮询任务，以便在需要时可以取消
    return polling_task

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