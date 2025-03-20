import asyncio
import logging
from bot import start_bot  # ✅ 这里修改：导入 `start_bot()` 作为异步函数
from task_scheduler import job  # ✅ 只导入 `job`，不导入 `scheduler`

# 设置日志
# logging.basicConfig(level=logging.INFO)
# logging.info("🚀 Bot and Scheduler are starting...")

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # ✅ 隐藏 httpx 的 INFO 日志
logging.info("🚀 Bot and Scheduler are starting...")

async def run_scheduler():
    """
    1. 每 30 分钟执行一次任务（不再在这里执行首次任务）
    """
    while True:
        logging.info("⏳ 等待 30 分钟后执行下一次任务...")
        await asyncio.sleep(30 * 60)  # ✅ 每 30 分钟运行一次
        logging.info("🔍 开始执行定时任务...")
        await job()

async def main():
    """
    1. 启动 Telegram 机器人
    2. 立即执行一次定时任务
    3. 启动定时任务（每 30 分钟执行）
    """    
    logging.info("✅ 启动 Telegram Bot 和定时任务...")

    # ✅ **1️⃣ 先执行一次 `job()`**
    logging.info("🔍 **首次执行 job()**")
    await job()
    logging.info("✅ 首次任务 job() 执行完成")

    # ✅ **2️⃣ 并行启动 Bot 和定时任务**
    bot_task = asyncio.create_task(start_bot())  
    scheduler_task = asyncio.create_task(run_scheduler())  

    # ✅ 让两个任务并行
    await asyncio.gather(bot_task, scheduler_task)  

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())  # ✅ 不会触发 `RuntimeError`
        # asyncio.run(main())  # ✅ 运行主协程
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            logging.warning("⚠️ 事件循环已在运行，切换到 `asyncio.create_task()`")
            asyncio.create_task(main())  # ✅ 兼容 Jupyter Notebook 或其他环境
            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(main())  # ✅ 兼容 Jupyter Notebook 或其他环境
        else:
            raise