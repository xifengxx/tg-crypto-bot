import asyncio
import logging
import os
import signal
import sys

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 全局变量，用于存储应用实例和调度器
application = None
scheduler = None

# 信号处理函数
def signal_handler(sig, frame):
    """
    处理程序退出信号
    """
    logger.info("接收到退出信号，正在关闭程序...")
    
    # 关闭调度器
    if scheduler:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")
    
    # 取消轮询任务
    if 'polling_task' in globals() and polling_task:
        polling_task.cancel()
        logger.info("Telegram Bot 轮询任务已取消")
    
    # 退出程序
    sys.exit(0)

# 修改 main 函数，避免使用 Playwright
# 在 main 函数中修改环境变量设置部分
async def main():
    """
    主函数，协调各个模块的运行
    """
    global application, scheduler, polling_task
    
    try:
        # 注册信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 检查运行环境并输出明确标识
        is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
        environment_name = "Railway环境" if is_railway else "本地环境"
        logger.info(f"🌍 当前在【{environment_name}】中运行程序")
        
        # 导入必要的模块
        from news_database import news_collection
        from bot import send_latest_news, start_bot
        from task_scheduler import start_scheduler
        
        # 启动 Telegram Bot
        polling_task = await start_bot()
        logger.info("Telegram Bot 已启动")
        
        # 检查是否在 Railway 环境中运行
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            logger.info("在 Railway 环境中运行")
            
            # 删除以下两行代码
            # os.environ['USE_BACKUP_SCRAPER'] = 'true'
            # logger.info("Railway 环境下，将使用备用的抓取方法")
            
            # 打印所有环境变量，帮助调试
            logger.info("环境变量列表:")
            for key, value in os.environ.items():
                if not key.startswith('PATH') and not key.startswith('LD_'):
                    logger.info(f"  {key}: {value}")
        
        # 启动定时任务调度器
        scheduler = start_scheduler()
        logger.info("定时任务调度器已启动")
        
        # 立即执行一次抓取任务
        logger.info("开始执行首次抓取任务...")
        
        # 导入 scraper_main
        from news_scraper import main as scraper_main
        news_list = await scraper_main()
        logger.info(f"首次抓取完成，获取到 {len(news_list)} 条新闻")
        
        # 从 news_database 导入 store_news
        from news_database import store_news
        new_count = store_news(news_list)
        
        # 只有当有新内容时才发送
        if new_count > 0:
            logger.info(f"发现 {new_count} 条新新闻，准备推送...")
            await send_latest_news()
        else:
            logger.info("无新内容，跳过推送")
        
        # 保持程序运行
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次
            
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        logger.exception("详细错误信息")
        raise

    # 返回 polling_task，以便在程序退出时可以取消
    return polling_task

if __name__ == "__main__":
    asyncio.run(main())