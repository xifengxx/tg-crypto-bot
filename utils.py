# utils.py
import signal
from contextlib import contextmanager
import logging
import asyncio
from functools import wraps

# 设置日志
logger = logging.getLogger(__name__)

@contextmanager
def timeout(seconds):
    """
    超时处理上下文管理器（适用于同步代码）
    
    Args:
        seconds (int): 超时时间（秒）
    
    Raises:
        TimeoutError: 当执行时间超过指定秒数时抛出
    """
    def signal_handler(signum, frame):
        raise TimeoutError(f"执行超时，已超过 {seconds} 秒")

    # 设置信号处理器
    signal.signal(signal.SIGALRM, signal_handler)
    # 设置闹钟
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # 取消闹钟
        signal.alarm(0)

def async_timeout(seconds):
    """
    异步函数的超时装饰器
    
    Args:
        seconds (int): 超时时间（秒）
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                logger.error(f"函数 {func.__name__} 执行超时，已超过 {seconds} 秒")
                return []  # 返回空列表，避免后续处理出错
        return wrapper
    return decorator