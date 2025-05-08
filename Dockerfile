# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    # 添加以下可能缺失的依赖 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    fonts-noto-color-emoji \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量（在安装Playwright之前）
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV NODE_OPTIONS="--max-old-space-size=512"
ENV RAILWAY_ENVIRONMENT=true
ENV PYTHONUNBUFFERED=1

# 安装 Playwright 及其依赖（确保在设置环境变量之后）
RUN pip install playwright && \
    python -m playwright install --with-deps chromium

# 复制项目文件
COPY . .

# 启动命令
CMD ["python", "main.py"]