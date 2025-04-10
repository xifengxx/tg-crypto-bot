# news_scraper.py
import aiohttp
import asyncio
import requests  # 添加 requests 库导入
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from datetime import datetime, timedelta

# Binance新闻抓取示例
async def fetch_binance_news():
    url = "https://www.binance.com/en/support/announcement/c-48"
    news_list = []  # 将 news_list 移到函数开始处

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        try:
            print("正在加载 Binance 页面...")
            
            # 设置请求拦截
            await page.route("**/*", lambda route: route.continue_())
            
            # 增加加载超时时间，等待验证码加载
            await page.goto(url, wait_until="networkidle", timeout=120000)
            print("页面初步加载完成")
            
            # 等待页面加载完成
            await page.wait_for_timeout(5000)
            
            # 使用更精确的选择器
            selector = "div.bn-flex.flex-col.py-6"
            print(f"等待选择器: {selector}")
            await page.wait_for_selector(selector, timeout=60000)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            print("🔍 开始抓取 Binance 的新闻...")
            print(html[:100])  # 只打印HTML的前1000个字符

            # 更新选择器
            news_items = soup.select("div.bn-flex a.text-PrimaryText")
            print(f"找到 {len(news_items)} 个新闻项")
            
            # news_items = soup.select("div.items-center")
            # news_items = soup.select("div.flex-col.items-center a.text-primaryText")
            # news_items = soup.select("div.bn-flex a.text-primaryText")
            # news_list = []
            
            for item in news_items:
                title = None  # 初始化 title 为空
                # h3_items = item.find_all("h3", class_=["typography-body1-1", "typography-body3"])
                h3_items = item.find("h3", class_="typography-body1-1")
                title = h3_items.text.strip() if h3_items else None
                # title = h3_items[0].text.strip() if h3_items else None
                # if h3_items:
                #      title = h3_items[0].text.strip()
                
                link = "https://www.binance.com" + item["href"] if item.get("href") else None
            
                # 获取时间信息，使用提供的选择器
                time_tag = item.find_next("div", class_="typography-caption1")  # 查找紧邻的时间元素
                time = time_tag.text.strip() if time_tag else "No date found"
            
                 # 只在链接存在时添加到新闻列表
                if title and link and time:
                    news_list.append({
                        "title": title, 
                        "link": link, 
                        "time": format_news_time(time),
                        "source": "Binance"
                    })
                else:
                    print(f"⚠️ 跳过无效新闻项: {item}")
            
            await browser.close()
        except Exception as e:
            print(f"Binance 抓取出错: {e}")
            print(f"\n错误详细信息:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
        finally:
            await browser.close()
        
    # 将统计信息移到 async with 块外面，与函数的缩进级别相同
    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)
    
    print("\n=== 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")
    
    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")
    
    return list(unique_news)    


# 你可以为其它交易所编写类似的抓取函数
# OKX新闻抓取示例
async def fetch_okx_news():
    url = "https://www.okx.com/help/section/announcements-new-listings"
    news_list = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("正在加载 OKX 页面...")
            # 增加超时时间到 120 秒
            await page.goto(url, wait_until="domcontentloaded", timeout=120000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            await page.wait_for_selector("li.index_articleItem__d-8iK", timeout=60000)
            
            # 获取页面 HTML
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            print("🔍 开始抓取 OKX 的新闻...")
            print(html[:100])  # 只打印HTML的前1000个字符
            # 获取所有新闻项
            news_items = soup.select("li.index_articleItem__d-8iK")
            print(f"抓取到 {len(news_items)} 条新闻")
            news_list = []
            
            for item in news_items:
                title = None  # 初始化 title 为空
                title_tag = item.find("div", class_="index_title__iTmos")
                title = title_tag.text.strip() if title_tag else None

                link_tag = item.find("a", href=True)
                link = link_tag["href"] if link_tag else None

                # 获取时间信息
                time_tag = item.find("span", {"data-testid": "DateDisplay"})  # 根据 data-testid 属性获取时间
                time = time_tag.text.strip() if time_tag else "No date found"

                # 打印新闻的时间格式
                # print(f"抓取到的时间: {time}")
                
                # 只在链接存在时添加到新闻列表
                if title and link and time:
                    full_link = "https://www.okx.com" + link if not link.startswith("http") else link
                    # news_list.append({"title": title, "link": full_link, "time": time})
                    news_list.append({
                          "title": title, 
                          "link": full_link, 
                          "time": format_news_time(time),
                          "source": "OKX"
                        })
                else:
                    print(f"⚠️ 跳过无效新闻项: {item}")

            await browser.close()

        except Exception as e:
            print(f"OKX 抓取出错: {e}")
        finally:
            await browser.close()

    # 统计信息
    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)

    print("\n=== 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")

    return list(unique_news)

# Bitget新闻抓取
async def fetch_bitget_news():
    url = "https://www.bitget.com/support/categories/11865590960081"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        # 尝试跳过防爬虫检查
        await page.goto(url, wait_until="domcontentloaded")

        # 等待 Spot 和 Futures 区域加载
        try:
            await page.wait_for_selector("section.ArticleList_item_pair__vmMrx", timeout=90000)  # 增加超时
        except Exception as e:
            print(f"错误：{e}")
            html = await page.content()
            print(html[:1000])  # 输出HTML的前1000个字符以帮助调试

        # 获取页面 HTML
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        # 打印部分 HTML 内容来调试
        print("🔍 开始抓取 Bitget 的新闻...")
        print(html[:100])  # 只打印HTML的前1000个字符

        # 获取 Spot 和 Futures 上币信息
        spot_items = soup.select('section.ArticleList_item_pair__vmMrx')
        news_list = []

        # 处理 Spot 类型的新闻
        for item in spot_items:
            title = None
            link = None
            time = "No date found"
            
            # 获取标题和链接
            title_tag = item.find("span", class_="ArticleList_item_title__u3fLL")
            if title_tag:
                title = title_tag.get_text(strip=True)
                link_tag = title_tag.find("a", href=True)
                if link_tag:
                    link = "https://www.bitget.com" + link_tag["href"] if not link_tag["href"].startswith("http") else link_tag["href"]
            
            # 获取时间
            time_tag = item.find("div", class_="ArticleList_item_date__nEqio")
            if time_tag:
                time = time_tag.get_text(strip=True)

            # 只在有有效标题、链接和时间时添加到列表
            if title and link:
                # news_list.append({"title": title, "link": link, "time": time})
                news_list.append({
                      "title": title, 
                      "link": link, 
                      "time": format_news_time(time),
                      "source": "Bitget"
                    })

        await browser.close()

    # 统计信息
    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)

    # 输出结果
    print("\n=== 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")

    return list(unique_news)


# # Bybit新闻抓取 - 旧版本，使用网页抓取，现已注释掉
# 备份，Bybit新闻抓取 headless=False时OK，headless=True时报错 
# async def fetch_bybit_news():
#     url = "https://announcements.bybit.com/?category=new_crypto&page=1"
#     news_list = []
#     async with async_playwright() as p:
#         # browser = await p.chromium.launch(headless=False)
#         browser = await p.chromium.launch(
#             headless=False,
#             args=[      
#                 "--disable-blink-features=AutomationControlled",
#                 "--no-sandbox",
#                 "--disable-setuid-sandbox",
#                 "--disable-http2",
#                 "--disable-cache",
#                 "--disable-web-security",
#                 "--disable-gl",
#                 "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#             ]
#         )
#         page = await browser.new_page()

#         # # 尝试跳过防爬虫检查
#         try:
#             print("正在加载页面...")
#             await page.goto(url, wait_until="domcontentloaded", timeout=240000)
#             await page.wait_for_load_state("networkidle", timeout=60000)  # 等待网络闲置
#             # await page.goto(url, wait_until="networkidle", timeout=240000)  # 更长的超时
#             # 等待页面完全加载后再进行后续操作
#             await page.wait_for_selector("div.article-list", timeout=60000)  # 等待元素加载
#             print("页面加载完成，开始抓取内容...")
#         except Exception as e:
#             print(f"加载页面时出现错误: {e}")
#             html = await page.content()
#             print("页面HTML前1000个字符:")
#             print(html[:1000])  # 输出HTML的前1000个字符以帮助调试


#         # 获取页面 HTML
#         html = await page.content()
#         soup = BeautifulSoup(html, "html.parser")
#         # 打印部分 HTML 内容来调试
#         print("🔍 开始抓取 Bybit 的新闻...")
#         print(html[:100])  # 只打印HTML的前1000个字符
        
#         # 获取所有新闻项
#         news_items = soup.select("div.article-list a")
#         news_list = []
        
#         for item in news_items:
#             title = None  # 初始化 title 为空
#             link = item["href"] if item.get("href") else None
            
#             # 获取标题
#             title_tag = item.find("span")
#             title = title_tag.text.strip() if title_tag else None
            
#             # 获取时间
#             time_tag = item.find("div", class_="article-item-date")
#             time = time_tag.text.strip() if time_tag else "No date found"
            
#             # 只在链接存在时添加到新闻列表
#             if title and link:
#                 full_link = "https://announcements.bybit.com" + link if not link.startswith("http") else link
#                 # news_list.append({"title": title, "link": full_link, "time": time})
#                 news_list.append({
#                       "title": title, 
#                       "link": full_link, 
#                       "time": format_news_time(time),
#                       "source": "Bybit"
#                     })

#         await browser.close()

#     # 统计信息
#     total_count = len(news_list)
#     unique_news = {item["title"]: item for item in news_list}.values()
#     filtered_count = len(unique_news)

#     print("\n=== 抓取统计 ===")
#     print(f"📌 总共抓取 {total_count} 条新闻")
#     print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

#     print("\n=== 抓取结果 ===\n")
#     for item in unique_news:
#         print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")

#     return list(unique_news)

# 使用 Bybit 官方 API 获取新闻
async def fetch_bybit_news():
    print("开始通过 Bybit 官方 API 抓取新闻...")
    news_list = []
    
    # 导入 requests 库
    import requests
    
    # Bybit 公告 API 官方端点
    url = "https://api.bybit.com/v5/announcements/index"
    
    # 请求参数 (根据官方文档)
    params = {
        "locale": "en-US",  # 使用英文，更稳定
        "type": "new_crypto",  # 新币上线类别
        "page": 1,
        "limit": 20  # 获取最新的20条公告
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        print(f"正在请求 Bybit API: {url}")
        
        # 使用同步请求，设置较长的超时时间
        response = requests.get(url, params=params, headers=headers, timeout=60)
        
        print(f"API 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 检查 API 响应结构 (根据官方文档)
            if data.get("retCode") == 0 and "result" in data:
                result = data["result"]
                announcements = result.get("list", [])
                print(f"获取到 {len(announcements)} 条公告")
                
                for item in announcements:
                    title = item.get("title")
                    url = item.get("url")
                    publish_time = item.get("publishTime")
                    description = item.get("description", "")
                    
                    if title:
                        # 处理时间
                        formatted_time = None
                        if publish_time:
                            try:
                                # API 返回的时间通常是毫秒级时间戳
                                dt = datetime.fromtimestamp(int(publish_time) / 1000)
                                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                            except Exception as e:
                                print(f"时间格式化错误: {e}, 原始时间: {publish_time}")
                                formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                        
                        news_list.append({
                            "title": title,
                            "link": url,
                            "time": formatted_time,
                            "description": description,
                            "source": "Bybit"
                        })
                        print(f"✅ 成功抓取: {title} | 时间: {formatted_time}")
            else:
                error_msg = data.get("retMsg", "未知错误")
                print(f"API 响应错误: {error_msg}")
                print(f"完整响应: {data}")
        else:
            print(f"API 请求失败，状态码: {response.status_code}")
            print(response.text)
    except requests.exceptions.Timeout:
        print("API 请求超时，尝试备用端点...")
        # 尝试备用端点
        backup_url = "https://api.bytick.com/v5/announcements/index"
        try:
            response = requests.get(backup_url, params=params, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if data.get("retCode") == 0 and "result" in data:
                    result = data["result"]
                    announcements = result.get("list", [])
                    print(f"备用 API 获取到 {len(announcements)} 条公告")
                    
                    for item in announcements:
                        title = item.get("title")
                        url = item.get("url")
                        publish_time = item.get("publishTime")
                        description = item.get("description", "")
                        
                        if title:
                            # 处理时间
                            formatted_time = None
                            if publish_time:
                                try:
                                    dt = datetime.fromtimestamp(int(publish_time) / 1000)
                                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                                except Exception as e:
                                    print(f"时间格式化错误: {e}, 原始时间: {publish_time}")
                                    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                            
                            news_list.append({
                                "title": title,
                                "link": url,
                                "time": formatted_time,
                                "description": description,
                                "source": "Bybit"
                            })
                            print(f"✅ 成功抓取: {title} | 时间: {formatted_time}")
                else:
                    print(f"备用 API 响应错误: {data.get('retMsg', '未知错误')}")
            else:
                print(f"备用 API 请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"备用 API 抓取出错: {e}")
    except Exception as e:
        print(f"Bybit API 抓取出错: {e}")
        print(f"\n错误详细信息:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
    
    # 统计信息
    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)

    print("\n=== Bybit 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")

    return list(unique_news)

# 统一处理新闻时间格式
def format_news_time(news_time):
    """
    统一处理新闻时间的格式
    支持多种格式：
    1. '2025-02-27'
    2. 'Published on Feb 20, 2025'
    3. '2025-03-03 10:41'
    4. 'Feb 26, 2025'
    5. '03/12/2025, 03:12:02'
    6. '1 hours 6 min 16 sec ago'
    7. '2 days ago'
    8. '3 minutes ago'
    返回统一格式的时间：'YYYY-MM-DD HH:MM:SS UTC'
    """
    # 处理相对时间格式
    try:
        if "ago" in news_time.lower():
            now = datetime.now()
            parts = news_time.lower().split()
            
            if "day" in parts[1]:
                days = int(parts[0])
                result_time = now - timedelta(days=days)
            elif "hour" in parts[1]:
                hours = int(parts[0])
                minutes = int(parts[2]) if len(parts) > 4 and "min" in parts[3] else 0
                result_time = now - timedelta(hours=hours, minutes=minutes)
            elif "minute" in parts[1] or "min" in parts[1]:
                minutes = int(parts[0])
                result_time = now - timedelta(minutes=minutes)
            elif "second" in parts[1] or "sec" in parts[1]:
                seconds = int(parts[0])
                result_time = now - timedelta(seconds=seconds)
            else:
                return now.strftime("%Y-%m-%d %H:%M:%S UTC")
                
            return result_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, IndexError):
        pass

    # 保留原有的格式处理代码
    try:
        if len(news_time) == 10:  # 格式 2025-02-27
            return datetime.strptime(news_time, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00 UTC")
    except ValueError:
        pass

    # 处理格式2: Published on Feb 20, 2025
    try:
        if news_time.startswith("Published on"):
            news_time = news_time[13:].strip()  # 去掉 "Published on"
            return datetime.strptime(news_time, "%b %d, %Y").strftime("%Y-%m-%d 00:00:00 UTC")
    except ValueError:
        pass
    # 处理格式3: 2025-03-03 10:41
    try:
        if len(news_time) > 10:  # 格式 2025-03-03 10:41
            return datetime.strptime(news_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        pass

    # 处理格式4: Feb 26, 2025
    try:
        if len(news_time.split()) == 3:  # 格式 Feb 26, 2025
            return datetime.strptime(news_time, "%b %d, %Y").strftime("%Y-%m-%d 00:00:00 UTC")
    except ValueError:
        pass
    
    # 处理格式5: 添加对 MM/DD/YYYY, HH:MM:SS 格式的支持
    try:
        if '/' in news_time and ',' in news_time:
            parsed_time = datetime.strptime(news_time.strip(), "%m/%d/%Y, %H:%M:%S")
            return parsed_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        pass
    
    print(f"❌ 无法解析时间: {news_time}")
    return None

    # 处理格式5: MM/DD/YYYY, HH:MM:SS 格式的支持
    # try:
    #     if '/' in news_time and ',' in news_time:
    #         date_part, time_part = news_time.split(',')
    #         parsed_time = datetime.strptime(news_time.strip(), "%m/%d/%Y, %H:%M:%S")
    #         return parsed_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    # except ValueError:
    #     pass


# 测试抓取功能
# Coinbase新闻抓取，Coinbase通过Twitter发布的消息，没有网页：https://x.com/CoinbaseAssets，https://x.com/CoinbaseIntExch
# async def fetch_coinbase_news():
#     url = "https://www.coinbase.com/browse/announcements"
#     news_list = []

#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
        
#         try:
#             print("正在加载 Coinbase 页面...")
#             await page.goto(url, wait_until="domcontentloaded", timeout=60000)
#             await page.wait_for_selector("article", timeout=60000)
            
#             html = await page.content()
#             soup = BeautifulSoup(html, "html.parser")
#             print("🔍 开始抓取 Coinbase 的新闻...")
            
#             news_items = soup.select("article")
            
#             for item in news_items:
#                 title_tag = item.find("h2")
#                 title = title_tag.text.strip() if title_tag else None
                
#                 link_tag = item.find("a", href=True)
#                 link = "https://www.coinbase.com" + link_tag["href"] if link_tag else None
                
#                 time_tag = item.find("time")
#                 time = time_tag["datetime"] if time_tag else "No date found"
                
#                 if title and link:
#                     news_list.append({
#                         "title": title,
#                         "link": link,
#                         "time": format_news_time(time),
#                         "source": "Coinbase"
#                     })
                    
#         except Exception as e:
#             print(f"Coinbase 抓取出错: {e}")
#         finally:
#             await browser.close()

#     # 统计信息
#     total_count = len(news_list)
#     unique_news = {item["title"]: item for item in news_list}.values()
#     filtered_count = len(unique_news)
    
#     print("\n=== Coinbase 抓取统计 ===")
#     print(f"📌 总共抓取 {total_count} 条新闻")
#     print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")
    
#     return list(unique_news)




# KuCoin新闻抓取
async def fetch_kucoin_news():
    url = "https://www.kucoin.com/announcement/new-listings"
    news_list = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("正在加载 KuCoin 页面...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_selector("ul.kux-e8uvvx", timeout=60000)
            
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            print("🔍 开始抓取 KuCoin 的新闻...")
            
            # 获取所有新闻项
            news_items = soup.select("ul.kux-e8uvvx > li")
            
            for item in news_items:
                title = None  # 初始化 title 为空
                link = None
                time = "No date found"
                
                # 获取标题和链接
                link_tag = item.find("a", href=True)
                if link_tag:
                    link = "https://www.kucoin.com" + link_tag["href"]
                    title_tag = link_tag.find("span")
                    title = title_tag.text.strip() if title_tag else None
                
                # 获取时间
                time_tag = item.find("p", class_='kux-q65diy')
                time = time_tag.text.strip() if time_tag else "No date found"
                
                if title and link:
                    news_list.append({
                        "title": title,
                        "link": link,
                        "time": format_news_time(time),
                        "source": "KuCoin"
                    })
                    
        except Exception as e:
            print(f"KuCoin 抓取出错: {e}")
            html = await page.content()
            print("页面HTML前1000个字符:")
            print(html[:1000])
        finally:
            await browser.close()

    # 统计信息
    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)
    
    print("\n=== KuCoin 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")
    
    return list(unique_news)

# Gate.io新闻抓取
async def fetch_gate_news():
    url = "https://www.gate.io/announcements/newlisted"
    news_list = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # 减少内存使用
                "--disable-gpu",  # 禁用GPU加速
            ],
            timeout=120000  # 增加浏览器启动超时时间到2分钟
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        try:
            print("正在加载 Gate.io 页面...")
            # 设置请求拦截，类似于Binance的处理方式
            await page.route("**/*", lambda route: route.continue_())
            
            # 增加页面加载超时时间到2分钟
            await page.goto(url, wait_until="networkidle", timeout=120000)
            print("页面初步加载完成")
            
            # 等待页面加载完成
            await page.wait_for_timeout(5000)
            
            # 使用更精确的选择器
            selector = "div.flex.flex-col.gap-6.sm\\:gap-8 a"
            print(f"等待选择器: {selector}")
            await page.wait_for_selector(selector, timeout=60000)
            
            # 获取页面 HTML
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            print("🔍 开始抓取 Gate.io 的新闻...")
            print(f"页面HTML前100个字符: {html[:100]}")  # 打印页面开头部分
            # 获取所有新闻项，使用更精确的选择器
            news_items = soup.select("div.flex.flex-col.gap-6.sm\\:gap-8 a")
            # print(f"找到 {len(news_items)} 个新闻项")
            
            for item in news_items:
                title = None  # 初始化 title 为空
                link = None
                time = "No date found"
                
                # 获取标题
                title_tag = item.find("p", class_="font-medium text-subtitle line-clamp-2")
                title = title_tag.text.strip() if title_tag else None
                
                # 获取链接
                link = "https://www.gate.io" + item["href"] if item.get("href") else None
                
                # 获取时间 - 使用图片中显示的结构
                time_div = item.find("div", class_="flex gap-5 text-body-s text-t3")
                if time_div:
                    time_inner_div = time_div.find("div", class_="flex items-center gap-1")
                    if time_inner_div:
                        time_span = time_inner_div.find("span")
                        time = time_span.text.strip() if time_span else "No date found"
                
                if title and link:
                    news_list.append({
                        "title": title,
                        "link": link,
                        "time": format_news_time(time),
                        "source": "Gate.io"
                    })
                    # print(f"✅ 成功抓取: {title} | 时间: {time}")
                else:
                    print(f"⚠️ 跳过无效新闻项: 标题={title}, 链接={link}")
                    
        except Exception as e:
            print(f"Gate.io 抓取出错: {e}")
            print(f"\n错误详细信息:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            html = await page.content()
            print("页面HTML前1000个字符:")
            print(html[:1000])  # 输出HTML帮助调试
        finally:
            await browser.close()

    # 统计信息
    total_count = len(news_list)
    unique_news = {item["title"]: item for item in news_list}.values()
    filtered_count = len(unique_news)
    
    print("\n=== Gate.io 抓取统计 ===")
    print(f"📌 总共抓取 {total_count} 条新闻")
    print(f"🔍 去重后剩余 {filtered_count} 条新闻\n")

    print("\n=== 抓取结果 ===\n")
    for item in unique_news:
        print(f"📌 {item['title']}\n🔗 {item['link']}\n📅 {item['time']}\n")
    
    return list(unique_news)

# 更新 main 函数
async def main():
    print("抓取 Binance 新闻:")
    binance_news = await fetch_binance_news()
    
    print("抓取 OKX 新闻:")
    okx_news = await fetch_okx_news()

    print("抓取 Bitget 新闻:")
    bitget_news = await fetch_bitget_news()

    print("抓取 Bybit 新闻:")
    bybit_news = await fetch_bybit_news()

    # print("抓取 Coinbase 新闻:")
    # coinbase_news = await fetch_coinbase_news()

    print("抓取 KuCoin 新闻:")
    kucoin_news = await fetch_kucoin_news()

    print("抓取 Gate.io 新闻:")
    gate_news = await fetch_gate_news()

if __name__ == '__main__':
    asyncio.run(main())
