import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from sqlalchemy.orm import sessionmaker
from models import engine, Message, User, Group
from telegram import Update
from telegram.ext import ContextTypes
import jieba
from collections import Counter
from database import get_db

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 创建数据库会话
Session = sessionmaker(bind=engine)

class MessageAnalyzer:
    def __init__(self):
        self.session = Session()
    
    def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户统计数据"""
        try:
            # 获取用户最近30天的消息
            start_date = datetime.now() - timedelta(days=30)
            messages = self.session.query(Message).filter(
                Message.user_id == user_id,
                Message.created_at >= start_date
            ).all()
            
            if not messages:
                return None
            
            # 处理数据
            stats: Dict[str, Any] = {
                'total_messages': len(messages),
                'message_types': {},
                'active_groups': set(),
                'daily_stats': {},
                'last_active': None
            }
            
            for msg in messages:
                # 统计消息类型
                msg_type = msg.chat_type or 'text'
                stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
                
                # 记录活跃群组
                if msg.group_id:
                    stats['active_groups'].add(msg.group_id)
                
                # 统计每日消息
                date = msg.created_at.strftime('%Y-%m-%d')
                stats['daily_stats'][date] = stats['daily_stats'].get(date, 0) + 1
                
                # 更新最后活跃时间
                if not stats['last_active'] or msg.created_at > stats['last_active']:
                    stats['last_active'] = msg.created_at
            
            return stats
        except Exception as e:
            logger.error(f"获取用户统计数据失败: {e}")
            return None
    
    def get_group_stats(self, group_id: int) -> Optional[Dict[str, Any]]:
        """获取群组统计数据"""
        try:
            # 首先获取群组的内部ID
            group = self.session.query(Group).filter_by(telegram_id=group_id).first()
            if not group:
                return None
            
            # 获取群组最近30天的消息
            start_date = datetime.now() - timedelta(days=30)
            messages = self.session.query(Message).filter(
                Message.group_id == group.id,
                Message.created_at >= start_date
            ).all()
            
            if not messages:
                return None
            
            # 处理数据
            stats: Dict[str, Any] = {
                'total_messages': len(messages),
                'message_types': {},
                'active_users': set(),
                'daily_stats': {},
                'user_stats': {},
                'last_active': None
            }
            
            for msg in messages:
                # 统计消息类型
                msg_type = msg.chat_type or 'text'
                stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
                
                # 记录活跃用户
                stats['active_users'].add(msg.user_id)
                stats['user_stats'][msg.user_id] = stats['user_stats'].get(msg.user_id, 0) + 1
                
                # 统计每日消息
                date = msg.created_at.strftime('%Y-%m-%d')
                stats['daily_stats'][date] = stats['daily_stats'].get(date, 0) + 1
                
                # 更新最后活跃时间
                if not stats['last_active'] or msg.created_at > stats['last_active']:
                    stats['last_active'] = msg.created_at
            
            # 获取用户名
            user_ids = list(stats['user_stats'].keys())
            users = self.session.query(User).filter(User.id.in_(user_ids)).all()
            user_map = {user.id: user.username or f"用户{user.telegram_id}" for user in users}
            
            # 更新用户统计
            stats['user_stats'] = {user_map[uid]: count for uid, count in stats['user_stats'].items()}
            
            return stats
        except Exception as e:
            logger.error(f"获取群组统计数据失败: {e}")
            return None
    
    def analyze_keywords(self, group_id: int) -> Optional[Dict[str, Any]]:
        """分析关键词使用情况"""
        try:
            # 获取群组最近30天的消息
            start_date = datetime.now() - timedelta(days=30)
            messages = self.session.query(Message).filter(
                Message.group_id == group_id,
                Message.created_at >= start_date,
                Message.content.isnot(None)  # 只分析有内容的消息
            ).all()
            
            if not messages:
                return None
            
            # 分词并统计
            all_words = []
            for message in messages:
                if message.content:  # 再次检查内容是否为空
                    words = jieba.cut(message.content)
                    all_words.extend([w for w in words if len(w) > 1])  # 只统计长度大于1的词
            
            word_counts = Counter(all_words)
            
            return {
                'total_words': len(all_words),
                'unique_words': len(word_counts),
                'top_keywords': dict(word_counts.most_common(20))
            }
        except Exception as e:
            logger.error(f"分析关键词失败: {e}")
            return None
    
    def close(self) -> None:
        """关闭数据库会话"""
        self.session.close()

# 创建分析器实例
analyzer = MessageAnalyzer()

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理统计命令"""
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup', 'channel', 'private']:
        await update.message.reply_text("此命令只能在群组、频道或私聊中使用！")
        return
    
    try:
        if chat_type == 'private':
            # 私聊中显示用户在所有群组/频道的数据
            user_id = update.effective_user.id
            stats = get_user_stats(user_id)
            response = format_user_stats(stats)
        else:
            # 群组/频道中显示该群组/频道的数据
            group_id = update.effective_chat.id
            stats = analyzer.get_group_stats(group_id)
            response = format_group_stats(stats)
        
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"生成统计信息失败: {e}")
        await update.message.reply_text("生成统计信息时发生错误")

def get_user_stats(user_id: int) -> Optional[Dict]:
    """获取用户统计数据"""
    try:
        session = Session()
        # 获取用户最近30天的消息
        start_date = datetime.now() - timedelta(days=30)
        messages = session.query(Message).filter(
            Message.user_id == user_id,
            Message.created_at >= start_date
        ).all()
        
        if not messages:
            return None
        
        # 处理数据
        stats = {
            'total_messages': len(messages),
            'message_types': {},
            'active_groups': set(),
            'daily_messages': {},
            'last_active': None
        }
        
        for msg in messages:
            # 统计消息类型
            msg_type = msg.chat_type or 'text'
            stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
            
            # 记录活跃群组
            if msg.group_id:
                stats['active_groups'].add(msg.group_id)
            
            # 统计每日消息
            date = msg.created_at.date()
            stats['daily_messages'][date] = stats['daily_messages'].get(date, 0) + 1
            
            # 更新最后活跃时间
            if not stats['last_active'] or msg.created_at > stats['last_active']:
                stats['last_active'] = msg.created_at
        
        return stats
    except Exception as e:
        logger.error(f"获取用户统计数据失败: {e}")
        return None
    finally:
        session.close()

def get_group_stats(group_id: int) -> Optional[Dict]:
    """获取群组统计数据"""
    try:
        session = Session()
        # 首先获取群组的内部ID
        group = session.query(Group).filter_by(telegram_id=group_id).first()
        if not group:
            return None
            
        # 获取群组最近30天的消息
        start_date = datetime.now() - timedelta(days=30)
        messages = session.query(Message).filter(
            Message.group_id == group.id,
            Message.created_at >= start_date
        ).all()
        
        if not messages:
            return None
        
        # 处理数据
        stats = {
            'total_messages': len(messages),
            'message_types': {},
            'active_users': set(),
            'daily_messages': {},
            'last_active': None
        }
        
        for msg in messages:
            # 统计消息类型
            msg_type = msg.chat_type or 'text'
            stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
            
            # 记录活跃用户
            stats['active_users'].add(msg.user_id)
            
            # 统计每日消息
            date = msg.created_at.date()
            stats['daily_messages'][date] = stats['daily_messages'].get(date, 0) + 1
            
            # 更新最后活跃时间
            if not stats['last_active'] or msg.created_at > stats['last_active']:
                stats['last_active'] = msg.created_at
        
        return stats
    except Exception as e:
        logger.error(f"获取群组统计数据失败: {e}")
        return None
    finally:
        session.close()

def format_user_stats(stats: Dict) -> str:
    """格式化用户统计数据"""
    if not stats:
        return "没有找到用户统计数据"
    
    response = (
        f"📊 用户统计报告\n\n"
        f"总消息数: {stats['total_messages']}\n"
        f"活跃群组数: {len(stats['active_groups'])}\n"
        f"最后活跃时间: {stats['last_active'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"消息类型分布:\n"
    )
    
    for msg_type, count in stats['message_types'].items():
        response += f"- {msg_type}: {count}\n"
    
    return response

def format_group_stats(stats: Dict) -> str:
    """格式化群组统计数据"""
    if not stats:
        return "没有找到群组统计数据"
    
    response = (
        f"📊 群组统计报告\n\n"
        f"总消息数: {stats['total_messages']}\n"
        f"活跃用户数: {len(stats['active_users'])}\n"
        f"最后活跃时间: {stats['last_active'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"消息类型分布:\n"
    )
    
    for msg_type, count in stats['message_types'].items():
        response += f"- {msg_type}: {count}\n"
    
    return response 