import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from models import engine, Message, User, Group
from telegram import Update
from telegram.ext import ContextTypes

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 创建数据库会话
Session = sessionmaker(bind=engine)

class GroupMonitor:
    def __init__(self):
        self.session = Session()
        
    def check_message_activity(self, group_id: int, hours: int = 24) -> dict:
        """检查群组消息活跃度"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 获取指定时间内的消息数量
        message_count = self.session.query(Message).filter(
            Message.group_id == group_id,
            Message.created_at >= cutoff_time
        ).count()
        
        # 获取活跃用户数
        active_users = self.session.query(User).join(Message).filter(
            Message.group_id == group_id,
            Message.created_at >= cutoff_time
        ).distinct().count()
        
        return {
            'message_count': message_count,
            'active_users': active_users,
            'time_period': hours
        }
    
    def check_keyword_alerts(self, group_id: int) -> list:
        """检查关键词告警"""
        # TODO: 实现关键词告警检查
        return []
    
    def check_user_behavior(self, user_id: int, group_id: int) -> dict:
        """检查用户行为"""
        # 获取用户最近的消息
        recent_messages = self.session.query(Message).filter(
            Message.user_id == user_id,
            Message.group_id == group_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        # 分析用户行为
        behavior = {
            'message_frequency': len(recent_messages),
            'last_activity': recent_messages[0].created_at if recent_messages else None,
            'warning_count': 0  # TODO: 实现警告计数
        }
        
        return behavior
    
    async def send_alert(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
        """发送告警消息"""
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⚠️ 告警：{message}",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"发送告警消息失败: {str(e)}")
    
    def close(self):
        """关闭数据库会话"""
        self.session.close()

# 创建监控实例
monitor = GroupMonitor()

async def check_group_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """检查群组活跃度"""
    if not update.effective_chat.type == 'group':
        return
    
    group_id = update.effective_chat.id
    activity = monitor.check_message_activity(group_id)
    
    if activity['message_count'] < 10:  # 如果24小时内消息少于10条
        await monitor.send_alert(
            update,
            context,
            f"群组活跃度较低！\n"
            f"过去24小时消息数：{activity['message_count']}\n"
            f"活跃用户数：{activity['active_users']}"
        )

async def check_user_behavior_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """检查用户行为并发送告警"""
    if not update.effective_user:
        return
    
    user_id = update.effective_user.id
    group_id = update.effective_chat.id
    
    behavior = monitor.check_user_behavior(user_id, group_id)
    
    if behavior['warning_count'] > 3:  # 如果警告次数超过3次
        await monitor.send_alert(
            update,
            context,
            f"用户 {update.effective_user.full_name} 行为异常！\n"
            f"警告次数：{behavior['warning_count']}"
        ) 