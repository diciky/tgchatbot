# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    cron \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY main.py .
COPY models.py .
COPY utils.py .
COPY backup.py .
COPY cron_backup.sh .
COPY .env .
COPY webui ./webui
COPY . /app

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data

# 创建存储目录
RUN mkdir -p /vol1/1000/tg/{photo,video,document,audio,voice}

# 设置定时任务
RUN chmod +x /app/cron_backup.sh
RUN echo "0 3 * * * /app/cron_backup.sh" > /etc/cron.d/backup-cron
RUN chmod 0644 /etc/cron.d/backup-cron
RUN crontab /etc/cron.d/backup-cron

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# 设置Intel GPU支持
ENV LIBVA_DRIVER_NAME=iHD
ENV DISPLAY=:0

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["sh", "-c", "cron && python webui/app.py & python main.py"] 