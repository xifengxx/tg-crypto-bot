# news_database.py
import os
from pymongo import MongoClient
from config import MONGO_URI
from datetime import datetime  # 添加这一行

# 在文件开头添加
import os
from pymongo import MongoClient
from config import MONGO_URI

# 连接到 MongoDB
try:
    client = MongoClient(MONGO_URI)
    
    # 根据环境选择数据库名称
    db_name = "crypto_news" if os.environ.get('RAILWAY_ENVIRONMENT') else "crypto_news_local"
    db = client[db_name]
    
    # 创建集合
    news_collection = db["news"]
    
    # 创建索引以确保新闻标题的唯一性
    news_collection.create_index([("title", 1)], unique=True)
    
    print(f"✅ 成功连接到 MongoDB: {MONGO_URI}")
except Exception as e:
    print(f"❌ MongoDB 连接失败: {e}")
    # 创建一个备用的内存存储，以防数据库连接失败
    class FallbackCollection:
        def __init__(self):
            self.data = []
            
        def insert_one(self, document):
            self.data.append(document)
            return True
            
        def find(self, query=None):
            return self.data
            
        def create_index(self, *args, **kwargs):
            pass
    
    news_collection = FallbackCollection()
    print("⚠️ 使用内存存储作为备用")

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