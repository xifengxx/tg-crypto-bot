# lark_bot.py
import requests
import json
import logging
import os

# 设置日志
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试从 config 导入 LARK_WEBHOOK_URL，如果失败则使用环境变量
try:
    from config import LARK_WEBHOOK_URL
    logger.info("成功从 config.py 导入 LARK_WEBHOOK_URL")
except ImportError:
    logger.warning("无法导入 config 模块，将使用环境变量")
    # 从环境变量获取 LARK_WEBHOOK_URL
    LARK_WEBHOOK_URL = os.environ.get('LARK_WEBHOOK_URL')
    logger.info(f"使用环境变量中的 LARK_WEBHOOK_URL")

def send_news_to_lark(message):
    """
    发送消息到 Lark 机器人
    """
    if not LARK_WEBHOOK_URL:
        logger.warning("未配置 LARK_WEBHOOK_URL，跳过发送")
        return
    
    try:
        # 构建 Lark 消息
        payload = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        
        # 发送请求
        response = requests.post(
            LARK_WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )
        
        # 检查响应
        if response.status_code == 200:
            logger.info("成功发送消息到 Lark")
        else:
            logger.error(f"发送消息到 Lark 失败: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"发送消息到 Lark 出错: {e}")