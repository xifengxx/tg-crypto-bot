# news_database.py
import pymongo
from config import MONGO_URI
from datetime import datetime  # 添加这一行

# 连接到MongoDB
client = pymongo.MongoClient(MONGO_URI)

# 选择数据库
db = client['crypto_news']  # 这里选择的数据库名称是 'crypto_news'
news_collection = db['news']  # 选择的集合名称是 'news'

# 插入新闻到数据库
def store_news(news_list):
    """
    将新闻数据存入 MongoDB, 避免重复存储, 并返回新增条数
    """
    if not news_list:
        print("⚠️ 没有新的新闻需要存储")
        return 0  # ✅ 修改：返回 0，方便 `task_scheduler.py` 进行判断
    
    new_count = 0  # 记录新增条数
    for news in news_list:
        # 过滤重复数据（标题 + 链接）
        existing_news = news_collection.find_one({"title": news["title"], "link": news["link"]})
        
        if not existing_news:
            news["created_at"] = datetime.utcnow()  # 添加时间戳
            news_collection.insert_one(news)
            new_count += 1
        else:
            # 如果存在新闻，更新缺失的字段
            if "source" not in existing_news:
                existing_news["source"] = news.get("source", "Unknown")  # 默认值为 'Unknown'
            if "time" not in existing_news:
                existing_news["time"] = news.get("time", datetime.utcnow().isoformat())  # 默认当前时间
            news_collection.update_one({"_id": existing_news["_id"]}, {"$set": existing_news})

    print(f"✅ 存储完成：{new_count} 条新新闻存入数据库")
    return new_count  # ✅ 确保返回新增新闻的数量