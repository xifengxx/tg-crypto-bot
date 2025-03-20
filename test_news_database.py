

from news_scraper import fetch_binance_news
from news_database import store_news
import asyncio

async def test_store_news():
    print("\n=== 测试抓取并存储 Binance 新闻 ===\n")
    news_list = await fetch_binance_news()  # 抓取新闻
    store_news(news_list)  # 存入数据库

if __name__ == "__main__":
    asyncio.run(test_store_news())