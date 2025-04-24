
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from news_scraper import fetch_binance_news
from news_scraper import fetch_binance_news, fetch_okx_news, fetch_bitget_news, fetch_bybit_news, fetch_kucoin_news, fetch_gate_news

from news_database import store_news
from bot import send_latest_news  # ✅ 导入自动推送方法
import asyncio
import time


# 定时任务
async def job():
    """
    1. 抓取新闻
    2. 存入数据库（去重）
    3. **仅当有新内容时** 推送到 Telegram
    """
    print("🔍 开始抓取 Binance、OKX、Bitget、Bybit、KuCoin 和 Gate.io 的新闻...")

    # 并行抓取所有交易所的新闻
    binance_news = await fetch_binance_news()
    okx_news = await fetch_okx_news()
    bitget_news = await fetch_bitget_news()
    bybit_news = await fetch_bybit_news()
    kucoin_news = await fetch_kucoin_news()  # 新增
    gate_news = await fetch_gate_news()      # 新增
    
    # 合并所有新闻
    all_news = (
        binance_news + 
        okx_news + 
        bitget_news + 
        bybit_news + 
        kucoin_news +  # 新增
        gate_news      # 新增
    )
    
    # 存入数据库
    new_count = store_news(all_news)

    if new_count > 0:
        print(f"📢 发现 {new_count} 条新新闻，准备推送到 Telegram...")
        await send_latest_news()  # ✅ 只有有新内容时才推送
    else:
        print("⏳ 无新内容，跳过推送")
    



# 添加 start_scheduler 函数，同时保留原有功能

# task_scheduler.py
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from datetime import datetime

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 尝试导入所需模块
try:
    from news_scraper import main as scraper_main
    from news_database import store_news
    from bot import send_latest_news
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    # 创建备用函数
    async def scraper_main():
        logger.warning("无法导入 news_scraper 模块，返回空列表")
        return []
    
    def store_news(news_list):
        logger.warning("无法导入 news_database 模块，跳过存储")
        return 0
    
    async def send_latest_news():
        logger.warning("无法导入 bot 模块，跳过发送消息")

# 创建调度器
scheduler = AsyncIOScheduler()

# 定义任务函数
async def scheduled_task():
    """
    定时执行的任务：抓取新闻并发送
    """
    try:
        # 检查运行环境
        is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
        environment_name = "Railway环境" if is_railway else "本地环境"
        logger.info(f"🌍 当前在【{environment_name}】中执行定时任务")
        logger.info("开始执行定时抓取任务...")
        
        # 抓取新闻
        news_list = await scraper_main()
        logger.info(f"定时抓取完成，获取到 {len(news_list)} 条新闻")
        
        # 存储新闻并获取新增数量
        new_count = store_news(news_list)
        
        # 只有当有新内容时才发送
        if new_count > 0:
            logger.info(f"发现 {new_count} 条新新闻，准备推送...")
            await send_latest_news()
        else:
            logger.info("无新内容，跳过推送")
            
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")
        logger.exception("详细错误信息")

def start_scheduler():
    """
    启动定时任务调度器
    """
    # 添加定时任务，每30分钟执行一次
    scheduler.add_job(scheduled_task, 'interval', minutes=30, id='news_scraper')
    
    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器已启动，每30分钟执行一次抓取任务")
    
    return scheduler

# 如果直接运行此文件，则启动调度器并保持运行
if __name__ == "__main__":
    # 创建事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # 启动调度器
    scheduler = start_scheduler()
    
    try:
        # 保持程序运行
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        # 关闭调度器
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")