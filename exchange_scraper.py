# exchange_scraper.py
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from datetime import datetime

class NewsScraperConfig:
    def __init__(self, name, url, selectors, base_url=None, timeout=60000, custom_headers=None):
        self.name = name
        self.url = url
        self.selectors = selectors
        self.base_url = base_url or url.split('/')[0] + '//' + url.split('/')[2]
        self.timeout = timeout
        self.custom_headers = custom_headers or {}

async def fetch_exchange_news(config: NewsScraperConfig):
    """统一的新闻抓取函数"""
    print(f"🔍 开始抓取 {config.name} 的新闻...")
    news_list = []

    async with async_playwright() as p:
        browser_options = {
            "headless": True
        }
        
        # Bybit 特殊配置
        if config.name == "Bybit":
            browser_options.update({
                "headless": False,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--disable-cache"
                ]
            })

        browser = await p.chromium.launch(**browser_options)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(config.url, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle", timeout=config.timeout)
            
            if config.selectors.get('wait_for'):
                await page.wait_for_selector(config.selectors['wait_for'], timeout=config.timeout)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            news_items = soup.select(config.selectors['list'])
            
            for item in news_items:
                news_data = extract_news_data(item, config)
                if news_data:
                    news_list.append(news_data)

        except Exception as e:
            print(f"❌ {config.name} 抓取出错: {e}")
        finally:
            await browser.close()

    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)

    print(f"\n=== {config.name} 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    return list(unique_news)

def extract_news_data(item, config):
    """提取新闻数据"""
    try:
        title_element = item.select_one(config.selectors['title']) if config.selectors.get('title') else item
        title = title_element.get_text(strip=True) if title_element else None

        link_element = item.select_one(config.selectors['link']) if config.selectors.get('link') else item
        link = link_element.get('href') if link_element else None
        if link and not link.startswith('http'):
            link = config.base_url + link

        time_element = item.select_one(config.selectors['time']) if config.selectors.get('time') else None
        time = time_element.get_text(strip=True) if time_element else "No date found"

        if title and link:
            return {
                "title": title,
                "link": link,
                "time": format_news_time(time),
                "source": config.name
            }
    except Exception as e:
        print(f"⚠️ 解析新闻项时出错: {e}")
    return None

def format_news_time(news_time):
    """统一处理新闻时间格式"""
    try:
        if len(news_time) == 10:  # 2025-02-27
            return datetime.strptime(news_time, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00 UTC")
        elif news_time.startswith("Published on"):
            news_time = news_time[13:].strip()
            return datetime.strptime(news_time, "%b %d, %Y").strftime("%Y-%m-%d 00:00:00 UTC")
        elif len(news_time) > 10:  # 2025-03-03 10:41
            return datetime.strptime(news_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S UTC")
        elif len(news_time.split()) == 3:  # Feb 26, 2025
            return datetime.strptime(news_time, "%b %d, %Y").strftime("%Y-%m-%d 00:00:00 UTC")
    except ValueError:
        print(f"❌ 无法解析时间: {news_time}")
    return None

# 交易所配置
EXCHANGE_CONFIGS = {
    "Binance": NewsScraperConfig(
        name="Binance",
        url="https://www.binance.com/en/support/announcement/c-48",
        selectors={
            "list": "div.bn-flex a.text-PrimaryText",
            "title": "h3.typography-body1-1",
            "time": "div.typography-caption1",
            "wait_for": "div.bn-flex"
        }
    ),
    "OKX": NewsScraperConfig(
        name="OKX",
        url="https://www.okx.com/help/section/announcements-new-listings",
        selectors={
            "list": "li.index_articleItem__d-8iK",
            "title": "div.index_title__iTmos",
            "time": "span[data-testid='DateDisplay']",
            "wait_for": "li.index_articleItem__d-8iK"
        },
        timeout=60000
    ),
    "Bitget": NewsScraperConfig(
        name="Bitget",
        url="https://www.bitget.com/support/categories/11865590960081",
        selectors={
            "list": "section.ArticleList_item_pair__vmMrx",
            "title": "span.ArticleList_item_title__u3fLL",
            "time": "div.ArticleList_item_date__nEqio",
            "wait_for": "section.ArticleList_item_pair__vmMrx"
        },
        timeout=90000
    ),
    "Bybit": NewsScraperConfig(
        name="Bybit",
        url="https://announcements.bybit.com/?category=new_crypto&page=1",
        selectors={
            "list": "div.article-list a",
            "title": "span",
            "time": "div.article-item-date",
            "wait_for": "div.article-list"
        },
        timeout=240000
    ),
    "KuCoin": NewsScraperConfig(
        name="KuCoin",
        url="https://www.kucoin.com/announcement/new-listings",
        selectors={
            "wait_for": "ul.kux-e8uvvx",
            "items": "ul.kux-e8uvvx > li",
            "title": "span",
            "link": "a",
            "time": "p.kux-q65diy"
        }
    ),
    "Gate.io": NewsScraperConfig(
        name="Gate.io",
        url="https://www.gate.io/announcements/newlisted",
        selectors={
            "wait_for": "div.article-list-box",
            "items": "div.article-list-item",
            "title": "span.overflow-ellipsis.article-list-item-title-con",
            "link": "a",
            "time": "span.article-list-info-timer"
        }
    )
}

async def main():
    """主函数"""
    for exchange_name, config in EXCHANGE_CONFIGS.items():
        print(f"\n开始抓取 {exchange_name} 新闻:")
        news = await fetch_exchange_news(config)
        print(f"✅ {exchange_name} 抓取完成\n")

if __name__ == "__main__":
    asyncio.run(main())