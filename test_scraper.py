
import asyncio
from news_scraper import fetch_binance_news

async def test():
    print("\n=== 测试所有交易所新闻抓取 ===")
    
    # 测试 KuCoin
    print("\n测试 KuCoin:")
    kucoin_news = await fetch_kucoin_news()
    print_stats(kucoin_news)
    
    # 测试 Gate.io
    print("\n测试 Gate.io:")
    gate_news = await fetch_gate_news()
    print_stats(gate_news)
    
    # 抓取新闻数据
    news = await fetch_binance_news()
    
    # 统计总抓取数
    total_count = len(news)
    
    # 去重（根据 title 进行去重）
    unique_news = {item["title"]: item for item in news}.values()
    
    # 统计去重后的数量
    filtered_count = len(unique_news)

    print("\n=== 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n")

if __name__ == "__main__":
    asyncio.run(test())