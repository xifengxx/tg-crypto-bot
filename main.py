import asyncio
import logging
from news_scraper import main as scraper_main
from news_database import news_collection
from bot import send_latest_news, start_bot
from task_scheduler import start_scheduler  # 现在这个导入应该能正常工作了
import os

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    """
    主函数，协调各个模块的运行
    """
    try:
        # 启动 Telegram Bot
        await start_bot()
        logger.info("Telegram Bot 已启动")
        
        # 检查是否在 Railway 环境中运行
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            logger.info("在 Railway 环境中运行")
            
            # 安装 Playwright 依赖
            import subprocess
            logger.info("安装 Playwright 依赖...")
            subprocess.run(["playwright", "install", "chromium"], check=True)
            logger.info("Playwright 依赖安装完成")
        
        # 启动定时任务调度器
        start_scheduler()
        logger.info("定时任务调度器已启动")
        
        # 立即执行一次抓取任务
        logger.info("开始执行首次抓取任务...")
        news_list = await scraper_main()
        logger.info(f"首次抓取完成，获取到 {len(news_list)} 条新闻")
        
        # 发送最新新闻
        await send_latest_news()
        
        # 保持程序运行
        while True:
            await asyncio.sleep(3600)  # 每小时检查一次
            
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())