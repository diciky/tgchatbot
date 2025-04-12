import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import sessionmaker
from models import engine, Message, User, Group
from telegram import Update
from telegram.ext import ContextTypes
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import pandas as pd
from database import get_db

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 创建数据库会话
Session = sessionmaker(bind=engine)

class DataVisualizer:
    def __init__(self):
        self.session = Session()
        
    def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户数据"""
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
            data: Dict[str, Any] = {
                'total_messages': len(messages),
                'message_types': {},
                'active_groups': set(),
                'daily_messages': {},
                'last_active': None
            }
            
            for msg in messages:
                # 统计消息类型
                msg_type = msg.chat_type or 'text'
                data['message_types'][msg_type] = data['message_types'].get(msg_type, 0) + 1
                
                # 记录活跃群组
                if msg.group_id:
                    data['active_groups'].add(msg.group_id)
                
                # 统计每日消息
                date = msg.created_at.date()
                data['daily_messages'][date] = data['daily_messages'].get(date, 0) + 1
                
                # 更新最后活跃时间
                if not data['last_active'] or msg.created_at > data['last_active']:
                    data['last_active'] = msg.created_at
            
            return data
        except Exception as e:
            logger.error(f"获取用户数据失败: {e}")
            return None
    
    def get_group_data(self, group_id: int) -> Optional[Dict[str, Any]]:
        """获取群组数据"""
        try:
            # 获取群组最近30天的消息
            start_date = datetime.now() - timedelta(days=30)
            messages = self.session.query(Message).filter(
                Message.group_id == group_id,
                Message.created_at >= start_date
            ).all()
            
            if not messages:
                return None
            
            # 处理数据
            data: Dict[str, Any] = {
                'total_messages': len(messages),
                'message_types': {},
                'active_users': set(),
                'daily_messages': {},
                'last_active': None
            }
            
            for msg in messages:
                # 统计消息类型
                msg_type = msg.chat_type or 'text'
                data['message_types'][msg_type] = data['message_types'].get(msg_type, 0) + 1
                
                # 记录活跃用户
                data['active_users'].add(msg.user_id)
                
                # 统计每日消息
                date = msg.created_at.date()
                data['daily_messages'][date] = data['daily_messages'].get(date, 0) + 1
                
                # 更新最后活跃时间
                if not data['last_active'] or msg.created_at > data['last_active']:
                    data['last_active'] = msg.created_at
            
            return data
        except Exception as e:
            logger.error(f"获取群组数据失败: {e}")
            return None
    
    def generate_charts(self, data: Dict[str, Any]) -> Optional[List[BytesIO]]:
        """生成图表"""
        try:
            charts: List[BytesIO] = []
            
            # 1. 消息类型分布饼图
            plt.figure(figsize=(10, 6))
            plt.pie(
                data['message_types'].values(),
                labels=data['message_types'].keys(),
                autopct='%1.1f%%'
            )
            plt.title('消息类型分布')
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            charts.append(buf)
            plt.close()
            
            # 2. 每日消息数量折线图
            plt.figure(figsize=(12, 6))
            dates = sorted(data['daily_messages'].keys())
            counts = [data['daily_messages'][date] for date in dates]
            plt.plot(dates, counts, marker='o')
            plt.title('每日消息数量')
            plt.xlabel('日期')
            plt.ylabel('消息数量')
            plt.xticks(rotation=45)
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            charts.append(buf)
            plt.close()
            
            return charts
        except Exception as e:
            logger.error(f"生成图表失败: {e}")
            return None
    
    async def send_charts(self, update: Update, context: ContextTypes.DEFAULT_TYPE, charts: List[BytesIO]) -> None:
        """发送图表"""
        try:
            for chart in charts:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=chart
                )
        except Exception as e:
            logger.error(f"发送图表失败: {e}")
    
    def close(self) -> None:
        """关闭数据库会话"""
        self.session.close()

# 创建可视化器实例
visualizer = DataVisualizer()

async def visualize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理可视化命令"""
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup', 'channel', 'private']:
        await update.message.reply_text("此命令只能在群组、频道或私聊中使用！")
        return
    
    try:
        if chat_type == 'private':
            # 私聊中显示用户在所有群组/频道的数据
            user_id = update.effective_user.id
            data = visualizer.get_user_data(user_id)
        else:
            # 群组/频道中显示该群组/频道的数据
            group_id = update.effective_chat.id
            data = visualizer.get_group_data(group_id)
        
        if not data:
            await update.message.reply_text("没有找到足够的数据来生成图表")
            return
        
        # 生成并发送图表
        charts = visualizer.generate_charts(data)
        if charts:
            await visualizer.send_charts(update, context, charts)
        else:
            await update.message.reply_text("生成图表时发生错误")
    except Exception as e:
        logger.error(f"生成可视化数据失败: {e}")
        await update.message.reply_text("生成可视化数据时发生错误") 