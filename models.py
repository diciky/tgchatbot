import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库文件路径
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'telegram_bot.db')

# 确保data目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# 创建数据库引擎
engine = create_engine(f'sqlite:///{DATABASE_PATH}', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_admin = Column(Boolean, default=False)
    points = Column(Integer, default=0)
    last_checkin = Column(DateTime)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String(6))  # 添加验证码字段
    warning_count = Column(Integer, default=0)  # 警告次数
    last_warning = Column(DateTime)  # 最后警告时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="user")
    groups = relationship("Group", secondary="user_groups", back_populates="users")

class Group(Base):
    """群组表"""
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(255))
    type = Column(String(50))
    is_monitoring = Column(Boolean, default=True)  # 是否启用监控
    min_activity_threshold = Column(Integer, default=10)  # 最低活跃度阈值
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="group")
    users = relationship("User", secondary="user_groups", back_populates="groups")

class Message(Base):
    """消息表"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'))
    content = Column(Text)
    chat_type = Column(String(50), default='text')
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 多媒体文件相关字段
    file_type = Column(String(50))  # 文件类型：photo, video, document, audio, voice
    file_id = Column(String(255))  # Telegram文件ID
    file_path = Column(String(512))  # 本地文件路径
    file_size = Column(Integer)  # 文件大小（字节）
    mime_type = Column(String(100))  # MIME类型
    
    user = relationship("User", back_populates="messages")
    group = relationship("Group", back_populates="messages")

class Keyword(Base):
    """关键词表"""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    word = Column(String)
    group_id = Column(Integer, ForeignKey('groups.id'))
    severity = Column(Integer, default=1)  # 严重程度：1-低，2-中，3-高
    is_active = Column(Boolean, default=True)  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)
    
    group = relationship("Group")

class Alert(Base):
    """告警表"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    alert_type = Column(String)  # 告警类型
    message = Column(String)  # 告警消息
    severity = Column(Integer, default=1)  # 严重程度
    is_resolved = Column(Boolean, default=False)  # 是否已解决
    resolved_at = Column(DateTime)  # 解决时间
    created_at = Column(DateTime, default=datetime.utcnow)
    
    group = relationship("Group")
    user = relationship("User")

class UserGroup(Base):
    __tablename__ = 'user_groups'
    
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    group_id = Column(Integer, ForeignKey('groups.id'), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

# 创建所有表
Base.metadata.create_all(engine) 