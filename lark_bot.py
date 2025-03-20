import requests
from config import LARK_WEBHOOK_URL  # 从 config.py 中获取 Lark Webhook URL

def send_lark_message(content):
    """
    向 Lark 群组发送消息
    :param content: 消息内容（支持 Markdown 格式）
    """
    if not LARK_WEBHOOK_URL:
        print("LARK Webhook URL is not set in config.py.")
        return

    headers = {"Content-Type": "application/json"}
    data = {
        "msg_type": "text",  # 消息类型为文本
        "content": {
            "text": content  # 消息内容
        }
    }
    try:
        response = requests.post(LARK_WEBHOOK_URL, json=data, headers=headers)
        if response.status_code == 200:
            print("Message sent to Lark successfully!")
        else:
            print(f"Failed to send message to Lark: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending message to Lark: {e}")

def split_message(content, max_length=4000):
    """
    将超长消息分割为多段
    :param content: 原始消息内容
    :param max_length: 每段的最大长度
    """
    return [content[i:i + max_length] for i in range(0, len(content), max_length)]

def send_news_to_lark(news_message):
    """
    将分块的消息发送到 Lark
    :param news_message: 完整的新闻内容
    """
    if not news_message:
        print("No news to send to Lark.")
        return

    # 分块消息
    messages = split_message(news_message)

    # 逐块发送
    for msg in messages:
        send_lark_message(msg)