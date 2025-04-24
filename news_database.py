# news_database.py
import os
from pymongo import MongoClient
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 修改 news_database.py 中获取 MongoDB URI 的部分

# 尝试从 config 导入 MONGO_URI，如果失败则使用环境变量
try:
    from config import MONGO_URI
    logger.info("成功从 config.py 导入 MONGO_URI")
except ImportError:
    logger.warning("无法导入 config 模块，将使用环境变量")
    
    # 从环境变量获取 MongoDB URI
    # Railway 提供的 MongoDB 服务会设置 MONGODB_URL 环境变量
    MONGO_URI = os.environ.get('MONGODB_URL') or os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
    
    # 打印 MongoDB URI 的一部分，避免泄露敏感信息
    if MONGO_URI:
        uri_parts = MONGO_URI.split('@')
        if len(uri_parts) > 1:
            masked_uri = f"{uri_parts[0].split('://')[0]}://***:***@{uri_parts[1]}"
        else:
            masked_uri = MONGO_URI
        logger.info(f"使用环境变量中的 MONGO_URI: {masked_uri}")
    
    # 检查 MongoDB URI 格式
    if not MONGO_URI or ':@:' in MONGO_URI:
        logger.error("MongoDB URI 格式不正确，使用默认本地连接")
        MONGO_URI = 'mongodb://localhost:27017'

# 连接到 MongoDB
try:
    # 检查运行环境
    is_railway = os.environ.get('RAILWAY_ENVIRONMENT') is not None
    environment_name = "Railway环境" if is_railway else "本地环境"
    logger.info(f"🌍 当前在【{environment_name}】中连接数据库")
    
    # 添加连接超时设置
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    
    # 测试连接
    client.admin.command('ping')
    
    # 根据环境选择数据库名称
    db_name = "crypto_news" if os.environ.get('RAILWAY_ENVIRONMENT') else "crypto_news_local"
    db = client[db_name]
    
    # 创建集合
    news_collection = db["news"]
    
    # 创建索引以确保新闻标题的唯一性
    news_collection.create_index([("title", 1)], unique=True)
    
    logger.info(f"✅ 成功连接到 MongoDB: {MONGO_URI}")
except Exception as e:
    logger.error(f"❌ MongoDB 连接失败: {e}")
    logger.exception("MongoDB 连接详细错误")
    
    # 创建一个备用的内存存储，以防数据库连接失败
    class FallbackCollection:
        def __init__(self):
            self.data = []
            
        def insert_one(self, document):
            self.data.append(document)
            return True
            
        def find(self, query=None):
            # 简单实现查询功能
            if not query:
                return self.data
            
            # 处理时间查询
            if query.get("created_at", {}).get("$gte"):
                min_time = query["created_at"]["$gte"]
                return [doc for doc in self.data if doc.get("created_at", datetime.min) >= min_time]
            
            return self.data
            
        def create_index(self, *args, **kwargs):
            pass
        
        def sort(self, field_name=None, direction=None):
            """
            模拟 MongoDB 的 sort 方法
            """
            # 简单实现，不做实际排序
            return self
        
        def find_one(self, query):
            """
            模拟 MongoDB 的 find_one 方法
            """
            for doc in self.data:
                match = True
                for key, value in query.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    return doc
            return None
        
        def update_one(self, filter_query, update_query):
            """
            模拟 MongoDB 的 update_one 方法
            """
            for doc in self.data:
                match = True
                for key, value in filter_query.items():
                    if key == "_id":
                        # 简单处理 _id 匹配
                        if str(doc.get("_id")) != str(value):
                            match = False
                            break
                    elif key not in doc or doc[key] != value:
                        match = False
                        break
                
                if match:
                    # 应用更新
                    if "$set" in update_query:
                        for key, value in update_query["$set"].items():
                            doc[key] = value
                    return True
            return False
    
    news_collection = FallbackCollection()
    logger.warning("⚠️ 使用内存存储作为备用")

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