from sqlalchemy.orm import sessionmaker
from models import engine, Message, User, Group
from datetime import datetime, timedelta

# 创建数据库会话
Session = sessionmaker(bind=engine)
session = Session()

def check_database():
    """检查数据库中的数据"""
    try:
        # 检查消息总数
        total_messages = session.query(Message).count()
        print(f"消息总数: {total_messages}")
        
        # 检查最近30天的消息
        start_date = datetime.now() - timedelta(days=30)
        recent_messages = session.query(Message).filter(
            Message.created_at >= start_date
        ).count()
        print(f"最近30天的消息数: {recent_messages}")
        
        # 检查用户总数
        total_users = session.query(User).count()
        print(f"用户总数: {total_users}")
        
        # 检查群组总数
        total_groups = session.query(Group).count()
        print(f"群组总数: {total_groups}")
        
        # 检查最新的几条消息
        print("\n最新的5条消息:")
        latest_messages = session.query(Message).order_by(Message.created_at.desc()).limit(5).all()
        for msg in latest_messages:
            print(f"ID: {msg.id}, 用户ID: {msg.user_id}, 群组ID: {msg.group_id}, 时间: {msg.created_at}, 类型: {msg.chat_type}")
        
    except Exception as e:
        print(f"检查数据库失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database() 