# utils.py
import signal
from contextlib import contextmanager
import logging

# 设置日志
logger = logging.getLogger(__name__)

@contextmanager
def timeout(seconds):
    """
    超时处理上下文管理器
    
    Args:
        seconds (int): 超时时间（秒）
    
    Raises:
        TimeoutError: 当执行时间超过指定秒数时抛出
    
    Example:
        with timeout(30):
            # 可能耗时较长的代码
            pass
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