
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
# 在文件顶部导入超时处理工具
from utils import timeout
import logging

logger = logging.getLogger(__name__)

# 修改定时任务函数
async def scheduled_task():
    """
    定时执行的任务，包含超时处理机制
    
    每30分钟执行一次，抓取新闻并推送到 Telegram 和 Lark
    如果执行时间超过25分钟，会自动终止任务
    """
    try:
        # 设置超时时间为25分钟（1500秒）
        # 由于任务间隔为30分钟，设置25分钟的超时确保下一个任务能正常执行
        with timeout(1500):
            logger.info("开始执行定时任务...")
            start_time = datetime.now()
            
            # 导入必要的模块
            from news_scraper import main as scraper_main
            from news_database import store_news
            from bot import send_latest_news
            
            try:
                # 抓取新闻，设置总超时为20分钟
                news_list = await asyncio.wait_for(scraper_main(), timeout=1200)
                logger.info(f"抓取完成，获取到 {len(news_list)} 条新闻")
                
                # 存储新闻
                new_count = store_news(news_list)
                
                # 推送新闻
                if new_count > 0:
                    logger.info(f"发现 {new_count} 条新新闻，准备推送...")
                    await send_latest_news()
                else:
                    logger.info("无新内容，跳过推送")
            except asyncio.TimeoutError:
                logger.error("新闻抓取超时，跳过本次任务")
                
            # 记录任务执行时间
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"定时任务执行完成，耗时 {duration:.2f} 秒")
            
    except TimeoutError as e:
        logger.error(f"定时任务执行超时: {e}")
        # 可以在这里添加清理代码，例如关闭连接等
    except Exception as e:
        logger.error(f"定时任务执行出错: {e}")
        logger.exception("详细错误信息")

def start_scheduler():
    """
    启动定时任务调度器
    """
    # 创建调度器实例
    scheduler = AsyncIOScheduler()
    
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