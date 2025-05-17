import os
import time
import threading
import subprocess
from datetime import datetime, timedelta
from news_scraper import clean_temp_files

# 获取重启间隔（小时）
restart_interval = int(os.environ.get('RESTART_INTERVAL_HOURS', '24'))

# 计算下次重启时间
next_restart = datetime.now() + timedelta(hours=restart_interval)

def check_restart():
    """
    检查是否需要重启应用
    """
    global next_restart
    while True:
        now = datetime.now()
        if now >= next_restart:
            print(f"已运行 {restart_interval} 小时，准备重启应用...")
            # 在重启前清理临时文件
            try:
                clean_temp_files()
                print("临时文件清理完成")
            except Exception as e:
                print(f"清理临时文件失败: {e}")
            # 在Railway环境中，退出进程会触发自动重启
            os._exit(0)
        
        # 每小时检查一次
        time.sleep(3600)

# 启动重启检查线程
restart_thread = threading.Thread(target=check_restart, daemon=True)
restart_thread.start()