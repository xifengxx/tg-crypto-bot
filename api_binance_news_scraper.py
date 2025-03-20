import requests
import logging
# 币安Announcement暂无API接口，无法通过调研API接口来获得上币信息

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# 设置你的API密钥（可选：如果需要身份验证）
API_KEY = "VMRMQ1MTyLWT2kkEgHv5du1kzZBCLWY9KlW54J4LKy7oH9AgNWYV1tzQAc5wr1MV"  # 替换为你的API密钥
BASE_URL = "https://api.binance.com/api/v3/announcement"

# 获取币安公告
def fetch_binance_news_api(limit=10, lang="en"):
    url = f"{BASE_URL}?limit={limit}&lang={lang}"
    headers = {"X-MBX-APIKEY": API_KEY}  # 如果需要API密钥，添加此头部
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败，则抛出异常
        announcements = response.json()  # 将返回的JSON数据转换为字典
        logging.info(f"成功抓取 {len(announcements)} 条公告")
        
        # 打印公告信息
        for ann in announcements:
            print(f"标题: {ann['title']}")
            print(f"链接: {ann['url']}")
            print(f"时间: {ann['date']}")
            print("-" * 50)
        
        return announcements  # 返回公告列表
    except requests.exceptions.RequestException as e:
        logging.error(f"抓取公告失败: {e}")
        return []

# 测试API抓取功能
if __name__ == "__main__":
    news = fetch_binance_news_api(limit=5)  # 获取最新的5条公告