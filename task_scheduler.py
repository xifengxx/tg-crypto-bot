
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
    



if __name__ == "__main__":
    loop = asyncio.new_event_loop()  # 创建一个新的事件循环
    asyncio.set_event_loop(loop)  # 设置当前事件循环为新创建的事件循环

    scheduler = AsyncIOScheduler(event_loop=loop)  # 将事件循环传递给调度器

    # ✅ 启动前先运行一次，然后每 30 分钟执行一次
    loop.run_until_complete(job())
    scheduler.add_job(job, 'interval', minutes=30)
    # scheduler.add_job(job, 'interval', hours=1)

    # 启动调度器
    scheduler.start()
    print("✅ 任务调度器已启动，每 30 分钟抓取 & 推送币安新闻")

    # 启动事件循环，保持任务运行
    loop.run_forever()