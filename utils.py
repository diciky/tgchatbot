import random
import string
from telegraph import Telegraph
from sqlalchemy.orm import sessionmaker
from models import engine, User, Group, Message, Keyword

# 创建数据库会话
Session = sessionmaker(bind=engine)

def generate_verification_code():
    """生成验证码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def create_telegraph_page(title, content):
    """创建Telegraph页面"""
    telegraph = Telegraph()
    telegraph.create_account(short_name='TelegramBot')
    
    response = telegraph.create_page(
        title=title,
        html_content=content
    )
    return response['url']

def add_points(user_id, points):
    """添加用户积分"""
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if user:
        user.points += points
        session.commit()
    session.close()

def check_keywords(message_text, group_id):
    """检查消息中是否包含关键词"""
    session = Session()
    keywords = session.query(Keyword).filter_by(group_id=group_id).all()
    found_keywords = []
    
    for keyword in keywords:
        if keyword.word.lower() in message_text.lower():
            found_keywords.append(keyword.word)
    
    session.close()
    return found_keywords

def save_message(message_id, user_id, group_id, content):
    """保存消息到数据库"""
    session = Session()
    
    # 确保用户存在
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        user = User(telegram_id=user_id)
        session.add(user)
        session.commit()
    
    # 确保群组存在
    group = session.query(Group).filter_by(telegram_id=group_id).first()
    if not group:
        group = Group(telegram_id=group_id)
        session.add(group)
        session.commit()
    
    # 保存消息
    message = Message(
        message_id=message_id,
        user_id=user.id,
        group_id=group.id,
        content=content
    )
    session.add(message)
    session.commit()
    session.close() 