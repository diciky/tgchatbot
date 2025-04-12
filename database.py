import os
from pymongo import MongoClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取MongoDB连接字符串
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/telegram_bot')

def get_db():
    """获取MongoDB数据库连接"""
    try:
        client = MongoClient(MONGODB_URI)
        db = client.get_database()
        return db
    except Exception as e:
        print(f"连接MongoDB失败: {e}")
        return None 