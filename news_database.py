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
    
    # 尝试删除可能存在的冲突索引
    try:
        news_collection.drop_index("title_1")
        logger.info("已删除旧的 title_1 索引")
    except Exception as e:
        logger.debug(f"删除索引时出错（可能不存在）: {e}")
    
    # 创建索引以确保新闻的唯一性，忽略不包含 unique_id 字段的文档
    news_collection.create_index([("unique_id", 1)], unique=True, sparse=True, name="unique_id_index")
    # 创建非唯一的标题索引，使用自定义名称避免冲突
    news_collection.create_index([("title", 1)], name="title_index_non_unique")
    
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
        
        def update_one(self, filter_query, update_query, upsert=False):
            """
            模拟 MongoDB 的 update_one 方法，支持 upsert 操作
            
            Args:
                filter_query (dict): 查询条件
                update_query (dict): 更新操作
                upsert (bool): 如果为 True，当文档不存在时插入新文档
            
            Returns:
                UpdateResult: 包含 upserted_id 属性的模拟更新结果对象
            """
            # 查找匹配的文档
            existing_doc = None
            for doc in self.data:
                match = True
                for key, value in filter_query.items():
                    if key not in doc or doc[key] != value:
                        match = False
                        break
                if match:
                    existing_doc = doc
                    break
            
            # 如果找到文档，更新它
            if existing_doc:
                if "$set" in update_query:
                    for key, value in update_query["$set"].items():
                        existing_doc[key] = value
                return type('UpdateResult', (), {'upserted_id': None})()
            
            # 如果没找到文档且 upsert=True，创建新文档
            elif upsert:
                new_doc = {}
                # 添加查询条件到新文档
                new_doc.update(filter_query)
                # 添加更新内容
                if "$set" in update_query:
                    new_doc.update(update_query["$set"])
                self.data.append(new_doc)
                return type('UpdateResult', (), {'upserted_id': id(new_doc)})()
            
            # 如果没找到文档且 upsert=False，返回无更新结果
            return type('UpdateResult', (), {'upserted_id': None})()
    
    news_collection = FallbackCollection()
    logger.warning("⚠️ 使用内存存储作为备用")

# 插入新闻到数据库
def store_news(news_list):
    """
    将新闻数据存入 MongoDB, 避免重复存储, 并返回新增条数
    
    Args:
        news_list (list): 新闻列表
        
    Returns:
        int: 新增的新闻数量
    """
    if not news_list:
        logger.info("⚠️ 没有新的新闻需要存储")
        return 0
    
    # 记录已处理的新闻标识，用于本次批量处理中的去重
    processed_ids = set()
    new_count = 0
    
    for news in news_list:
        try:
            # 确保必要字段存在
            if 'title' not in news or not news['title']:
                logger.warning(f"跳过无标题新闻: {news}")
                continue
                
            if 'source' not in news or not news['source']:
                news['source'] = "Unknown"
                
            # 生成唯一标识 - 只使用标题和来源，不使用时间
            # 这样即使时间不同，相同标题和来源的新闻也会被视为重复
            unique_id = f"{news['source']}_{news['title']}"
            
            # 检查是否在当前批次中已处理过
            if unique_id in processed_ids:
                logger.debug(f"当前批次中已处理过此新闻，跳过: {news['title']}")
                continue
            
            # 添加到已处理集合
            processed_ids.add(unique_id)
            
            # 先检查数据库中是否已存在
            existing_news = news_collection.find_one({
                "unique_id": unique_id
            })
            
            if existing_news:
                logger.info(f"新闻已存在于数据库，跳过: {news['title']}")
                continue
                
            # 使用 update_one 配合 upsert=True
            result = news_collection.update_one(
                {
                    "unique_id": unique_id
                },
                {
                    "$set": {
                        **news,
                        "unique_id": unique_id,  # 添加唯一标识
                        "created_at": datetime.utcnow(),
                        "source": news.get("source", "Unknown"),
                        "time": news.get("time", datetime.utcnow().isoformat()),
                        "last_updated": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # 如果是新插入的文档，增加计数
            if result.upserted_id:
                new_count += 1
                logger.info(f"新增新闻: {news['title']}")
                
        except Exception as e:
            logger.error(f"存储新闻时出错: {e}")
            logger.exception("详细错误信息")
            continue

    if new_count > 0:
        logger.info(f"✅ 存储完成：新增 {new_count} 条新闻")
    else:
        logger.info("✅ 存储完成：无新增新闻")
    return new_count