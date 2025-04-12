import os
import shutil
import datetime
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def backup_database():
    """备份数据库文件"""
    # 获取数据库路径
    db_path = os.getenv('DB_PATH', '/app/data/bot.db')
    backup_dir = os.getenv('BACKUP_DIR', '/app/data/backups')
    
    # 创建备份目录
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    # 生成备份文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'bot_{timestamp}.db')
    
    try:
        # 复制数据库文件
        shutil.copy2(db_path, backup_file)
        logger.info(f'数据库备份成功: {backup_file}')
        
        # 清理旧备份（保留最近7天的备份）
        cleanup_old_backups(backup_dir)
        
    except Exception as e:
        logger.error(f'数据库备份失败: {str(e)}')

def cleanup_old_backups(backup_dir, days_to_keep=7):
    """清理旧的备份文件"""
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=days_to_keep)
    
    for backup_file in Path(backup_dir).glob('bot_*.db'):
        file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
        if file_time < cutoff:
            try:
                backup_file.unlink()
                logger.info(f'删除旧备份: {backup_file}')
            except Exception as e:
                logger.error(f'删除旧备份失败: {str(e)}')

if __name__ == '__main__':
    backup_database() 