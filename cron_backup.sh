#!/bin/bash

# 设置环境变量
export DB_PATH=/app/data/bot.db
export BACKUP_DIR=/app/data/backups

# 执行备份
python /app/backup.py

# 记录日志
echo "$(date '+%Y-%m-%d %H:%M:%S') - 数据库备份完成" >> /app/data/backup.log 