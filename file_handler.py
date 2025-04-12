import os
import logging
from datetime import datetime
from typing import Optional, Tuple
from telegram import Update
from models import Message

# 配置日志
logger = logging.getLogger(__name__)

# 基础存储路径
BASE_STORAGE_PATH = "/vol1/1000/tg"

def get_file_info(update: Update) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[str]]:
    """获取文件信息"""
    message = update.message
    if not message:
        return None, None, None, None
    
    # 检查不同类型的文件
    if message.photo:
        file = message.photo[-1]  # 获取最高质量的照片
        file_type = "photo"
    elif message.video:
        file = message.video
        file_type = "video"
    elif message.document:
        file = message.document
        file_type = "document"
    elif message.audio:
        file = message.audio
        file_type = "audio"
    elif message.voice:
        file = message.voice
        file_type = "voice"
    else:
        return None, None, None, None
    
    return file_type, file.file_id, file.file_size, file.mime_type

def get_file_path(file_type: str, group_id: Optional[int] = None) -> str:
    """生成文件存储路径"""
    # 创建基础目录
    base_dir = os.path.join(BASE_STORAGE_PATH, file_type)
    os.makedirs(base_dir, exist_ok=True)
    
    # 如果有群组ID，创建群组子目录
    if group_id:
        group_dir = os.path.join(base_dir, str(group_id))
        os.makedirs(group_dir, exist_ok=True)
        return group_dir
    return base_dir

async def save_file(update: Update, context, file_type: str, file_id: str, group_id: Optional[int] = None) -> Optional[str]:
    """保存文件到本地"""
    try:
        # 获取文件
        file = await context.bot.get_file(file_id)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = os.path.splitext(file.file_path)[1] if file.file_path else ".bin"
        filename = f"{timestamp}_{file_id}{extension}"
        
        # 获取存储路径
        storage_path = get_file_path(file_type, group_id)
        file_path = os.path.join(storage_path, filename)
        
        # 下载文件
        await file.download_to_drive(file_path)
        
        logger.info(f"文件已保存: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return None

def update_message_with_file(message: Message, file_type: str, file_id: str, file_path: str, file_size: int, mime_type: str) -> None:
    """更新消息记录中的文件信息"""
    message.file_type = file_type
    message.file_id = file_id
    message.file_path = file_path
    message.file_size = file_size
    message.mime_type = mime_type 