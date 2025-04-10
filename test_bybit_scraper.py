# test_bybit_scraper.py
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

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

# Bybit新闻抓取 - 修改版本（headless=True）
# 修改 fetch_bybit_news 函数，使用 Chromium 而不是 Firefox
async def fetch_bybit_news():
    url = "https://announcements.bybit.com/?category=new_crypto&page=1"
    news_list = []
    
    print("开始抓取 Bybit 新闻...")
    
    async with async_playwright() as p:
        # 使用 headless=True 但添加更多反检测措施
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-http2",
                "--disable-cache",
                "--disable-web-security",
                "--disable-gl",
                # 添加更多参数来模拟真实浏览器
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-extensions",
                "--hide-scrollbars",
                "--disable-infobars",
                "--ignore-certificate-errors",
                "--allow-running-insecure-content",
            ]
        )
        
        # 创建更真实的浏览器上下文
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            # 添加更多浏览器特征
            device_scale_factor=2,
            is_mobile=False,
            has_touch=False,
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation"]
        )
        
        # 添加更多反检测脚本
        await context.add_init_script("""
            // 覆盖 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // 添加更多浏览器特征
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'zh-CN']
            });
            
            // 模拟 Chrome 插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // 覆盖 Permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
            
            // 添加 Canvas 指纹干扰
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function (x, y, w, h) {
                const imageData = originalGetImageData.call(this, x, y, w, h);
                const pixels = imageData.data;
                // 轻微修改像素值，但不明显改变图像
                for (let i = 0; i < pixels.length; i += 4) {
                    pixels[i] = pixels[i] + Math.floor(Math.random() * 2);
                    pixels[i+1] = pixels[i+1] + Math.floor(Math.random() * 2);
                    pixels[i+2] = pixels[i+2] + Math.floor(Math.random() * 2);
                }
                return imageData;
            };
        """)
        
        page = await context.new_page()
        
        # 模拟真实用户行为
        await page.mouse.move(100, 100)
        await page.mouse.down()
        # 修复：移除额外的参数，Python版本的move()不支持steps参数
        await page.mouse.move(200, 200)
        await page.mouse.up()

        try:
            print("正在加载 Bybit 页面...")
            
            # 使用代理（如果有）
            # await context.route('**/*', lambda route: route.continue_(
            #     headers={
            #         **route.request.headers,
            #         'X-Forwarded-For': '123.45.67.89'  # 随机 IP
            #     }
            # ))
            
            # 增加重试机制
            max_retries = 5  # 增加重试次数
            for attempt in range(max_retries):
                try:
                    print(f"尝试加载页面 (尝试 {attempt+1}/{max_retries})...")
                    
                    # 使用不同的加载策略
                    if attempt % 2 == 0:
                        await page.goto(url, wait_until="networkidle", timeout=90000)
                    else:
                        await page.goto(url, wait_until="load", timeout=90000)
                    
                    # 检查页面是否加载成功
                    content = await page.content()
                    if "article-list" in content:
                        print("页面成功加载，包含目标内容")
                        break
                    
                    print("页面加载完成，但未找到目标内容，将重试...")
                    await page.wait_for_timeout(3000 * (attempt + 1))  # 递增等待时间
                    
                except Exception as e:
                    print(f"加载页面失败: {e}")
                    if attempt == max_retries - 1:
                        raise
                    await page.wait_for_timeout(5000 * (attempt + 1))  # 递增等待时间
            
            print("页面初步加载完成")
            
            # 模拟用户滚动页面
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 300)")
                await page.wait_for_timeout(1000)
            
            # 等待页面加载完成
            await page.wait_for_timeout(5000)
            
            # 使用更精确的选择器
            selector = "div.article-list"
            print(f"等待选择器: {selector}")
            
            # 添加重试机制等待选择器
            for attempt in range(max_retries):
                try:
                    await page.wait_for_selector(selector, timeout=30000)
                    break
                except Exception as e:
                    print(f"等待选择器失败: {e}")
                    if attempt == max_retries - 1:
                        raise
                    
                    # 尝试刷新页面
                    if attempt > 1:
                        await page.reload(wait_until="networkidle")
                    
                    await page.wait_for_timeout(3000)
            
            # 确保页面稳定后再获取内容
            await page.wait_for_timeout(3000)
            
            # 尝试直接使用 JavaScript 获取内容
            news_data = await page.evaluate("""
                () => {
                    const items = Array.from(document.querySelectorAll('div.article-list a'));
                    return items.map(item => {
                        const titleEl = item.querySelector('span');
                        const timeEl = item.querySelector('div.article-item-date');
                        return {
                            title: titleEl ? titleEl.textContent.trim() : null,
                            link: item.href,
                            time: timeEl ? timeEl.textContent.trim() : 'No date found'
                        };
                    });
                }
            """)
            
            print(f"通过 JavaScript 找到 {len(news_data)} 个新闻项")
            
            # 如果 JavaScript 方法成功，使用它的结果
            if news_data and len(news_data) > 0:
                for item in news_data:
                    if item['title'] and item['link']:
                        news_list.append({
                            "title": item['title'], 
                            "link": item['link'], 
                            "time": format_news_time(item['time']),
                            "source": "Bybit"
                        })
                        print(f"✅ 成功抓取: {item['title']} | 时间: {item['time']}")
            else:
                # 备用方法：使用 BeautifulSoup
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                print("🔍 使用备用方法抓取 Bybit 的新闻...")
                
                # 获取所有新闻项
                news_items = soup.select("div.article-list a")
                print(f"找到 {len(news_items)} 个新闻项")
                
                for item in news_items:
                    title = None
                    link = item["href"] if item.get("href") else None
                    
                    title_tag = item.find("span")
                    title = title_tag.text.strip() if title_tag else None
                    
                    time_tag = item.find("div", class_="article-item-date")
                    time = time_tag.text.strip() if time_tag else "No date found"
                    
                    if title and link:
                        full_link = "https://announcements.bybit.com" + link if not link.startswith("http") else link
                        news_list.append({
                              "title": title, 
                              "link": full_link, 
                              "time": format_news_time(time),
                              "source": "Bybit"
                        })
                        print(f"✅ 成功抓取: {title} | 时间: {time}")
                    else:
                        print(f"⚠️ 跳过无效新闻项: 标题={title}, 链接={link}")
                    
        except Exception as e:
            print(f"Bybit 抓取出错: {e}")
            print(f"\n错误详细信息:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            
            try:
                await page.screenshot(path="/Users/mac/tg-crypto-bot/bybit_error.png")
                print("已保存错误页面截图到 bybit_error.png")
            except Exception as screenshot_error:
                print(f"无法保存截图: {screenshot_error}")
                
            try:
                html = await page.content()
                print("页面HTML前1000个字符:")
                print(html[:1000])
            except Exception as content_error:
                print(f"无法获取页面内容: {content_error}")
        finally:
            await browser.close()

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

# 使用 Bybit 官方 API 获取新闻 (使用同步 requests 库)
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
        
    # 如果主网和备用网都失败，尝试测试网
    if not news_list:
        try:
            print("\n尝试测试网 API...")
            test_url = "https://api-testnet.bybit.com/v5/announcements/index"
            response = requests.get(test_url, params=params, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("retCode") == 0 and "result" in data:
                    result = data["result"]
                    announcements = result.get("list", [])
                    print(f"测试网 API 获取到 {len(announcements)} 条公告")
                    
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
                    print(f"测试网 API 响应错误: {data.get('retMsg', '未知错误')}")
            else:
                print(f"测试网 API 请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"测试网 API 抓取出错: {e}")
    
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

# 添加一个调试函数来测试 Bybit API（使用同步的 requests 库）
def debug_bybit_api_sync():
    print("开始使用同步方式调试 Bybit API...")
    
    # 导入 requests 库
    import requests
    
    # Bybit 公告 API 官方端点
    url = "https://api.bybit.com/v5/announcements/index"
    
    # 请求参数 (根据官方文档)
    params = {
        "locale": "en-US",  # 使用英文
        "type": "new_crypto",  # 新币上线类别
        "page": 1,
        "limit": 5  # 只获取5条用于调试
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        print(f"正在请求 Bybit API: {url}")
        print(f"请求参数: {params}")
        
        # 设置较长的超时时间
        response = requests.get(url, params=params, headers=headers, timeout=60)
        
        print(f"API 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 打印完整的 API 响应
            # print("\n=== API 响应内容 ===")
            # print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 检查 API 响应结构
            if data.get("retCode") == 0 and "result" in data:
                result = data["result"]
                announcements = result.get("list", [])
                print(f"\n获取到 {len(announcements)} 条公告")
                
                # 打印第一条公告的详细信息
                if announcements:
                    print("\n=== 第一条公告详细信息 ===")
                    first_item = announcements[0]
                    for key, value in first_item.items():
                        print(f"{key}: {value}")
            else:
                error_msg = data.get("retMsg", "未知错误")
                print(f"API 响应错误: {error_msg}")
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
                print("\n=== 备用 API 响应内容 ===")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"备用 API 请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"备用 API 请求也失败: {e}")
    except Exception as e:
        print(f"调试过程出错: {e}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
    # 尝试第三个端点 - 测试网
    try:
        print("\n尝试测试网 API...")
        test_url = "https://api-testnet.bybit.com/v5/announcements/index"
        response = requests.get(test_url, params=params, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            print("\n=== 测试网 API 响应内容 ===")
            # print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"测试网 API 请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"测试网 API 请求失败: {e}")

# 修改测试函数
async def main():
    # 使用同步方式调试 API
    debug_bybit_api_sync()
    
    # 如果调试成功，再运行完整的抓取函数
    print("\n\n调试完成，开始运行完整抓取函数...\n")
    await fetch_bybit_news()

if __name__ == "__main__":
    asyncio.run(main())