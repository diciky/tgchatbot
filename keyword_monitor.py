import logging
import re
from typing import List, Dict, Set
from telegram import Update
from telegram.ext import ContextTypes
from database import get_db

logger = logging.getLogger(__name__)

class KeywordMonitor:
    def __init__(self):
        self.db = get_db()
        self.sensitive_words = set()  # 敏感词集合
        self.load_sensitive_words()
    
    def load_sensitive_words(self):
        """从数据库加载敏感词列表"""
        try:
            words = self.db.sensitive_words.find()
            self.sensitive_words = {word['word'] for word in words}
        except Exception as e:
            logger.error(f"加载敏感词失败: {e}")
            self.sensitive_words = set()
    
    def add_sensitive_word(self, word: str) -> bool:
        """添加敏感词"""
        try:
            if word not in self.sensitive_words:
                self.db.sensitive_words.insert_one({'word': word})
                self.sensitive_words.add(word)
                return True
            return False
        except Exception as e:
            logger.error(f"添加敏感词失败: {e}")
            return False
    
    def remove_sensitive_word(self, word: str) -> bool:
        """删除敏感词"""
        try:
            if word in self.sensitive_words:
                self.db.sensitive_words.delete_one({'word': word})
                self.sensitive_words.remove(word)
                return True
            return False
        except Exception as e:
            logger.error(f"删除敏感词失败: {e}")
            return False
    
    def check_sensitive_content(self, text: str) -> List[str]:
        """检查文本中的敏感词"""
        found_words = []
        for word in self.sensitive_words:
            if word in text:
                found_words.append(word)
        return found_words
    
    def analyze_user_behavior(self, user_id: int, group_id: int = None) -> Dict:
        """分析用户行为"""
        try:
            # 构建查询条件
            query = {'user_id': user_id}
            if group_id:
                query['group_id'] = group_id
            
            # 获取用户最近的消息
            recent_messages = list(self.db.messages.find(query).sort('timestamp', -1).limit(100))
            
            if not recent_messages:
                return {}
            
            # 分析消息特征
            total_messages = len(recent_messages)
            sensitive_count = 0
            keyword_count = 0
            message_types = {}
            
            for msg in recent_messages:
                # 检查敏感词
                if self.check_sensitive_content(msg.get('text', '')):
                    sensitive_count += 1
                
                # 统计消息类型
                msg_type = msg.get('type', 'text')
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            # 计算敏感词使用率
            sensitive_ratio = sensitive_count / total_messages if total_messages > 0 else 0
            
            return {
                'total_messages': total_messages,
                'sensitive_count': sensitive_count,
                'sensitive_ratio': sensitive_ratio,
                'message_types': message_types,
                'risk_level': self._calculate_risk_level(sensitive_ratio)
            }
        except Exception as e:
            logger.error(f"分析用户行为失败: {e}")
            return {}
    
    def _calculate_risk_level(self, sensitive_ratio: float) -> str:
        """计算风险等级"""
        if sensitive_ratio > 0.5:
            return "高风险"
        elif sensitive_ratio > 0.2:
            return "中风险"
        elif sensitive_ratio > 0:
            return "低风险"
        return "正常"

# 创建监控实例
monitor = KeywordMonitor()

async def add_sensitive_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """添加敏感词命令"""
    if not context.args:
        await update.message.reply_text("请提供要添加的敏感词！")
        return
    
    word = ' '.join(context.args)
    if monitor.add_sensitive_word(word):
        await update.message.reply_text(f"成功添加敏感词: {word}")
    else:
        await update.message.reply_text("添加敏感词失败或该词已存在")

async def remove_sensitive_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """删除敏感词命令"""
    if not context.args:
        await update.message.reply_text("请提供要删除的敏感词！")
        return
    
    word = ' '.join(context.args)
    if monitor.remove_sensitive_word(word):
        await update.message.reply_text(f"成功删除敏感词: {word}")
    else:
        await update.message.reply_text("删除敏感词失败或该词不存在")

async def check_behavior_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """检查用户行为命令"""
    if not update.effective_chat.type == 'group':
        await update.message.reply_text("此命令只能在群组中使用！")
        return
    
    user_id = update.effective_user.id
    group_id = update.effective_chat.id
    
    behavior = monitor.analyze_user_behavior(user_id, group_id)
    if not behavior:
        await update.message.reply_text("无法获取用户行为数据")
        return
    
    response = (
        f"📊 用户行为分析报告\n\n"
        f"总消息数: {behavior['total_messages']}\n"
        f"敏感词使用次数: {behavior['sensitive_count']}\n"
        f"敏感词使用率: {behavior['sensitive_ratio']:.2%}\n"
        f"风险等级: {behavior['risk_level']}\n\n"
        f"消息类型分布:\n"
    )
    
    for msg_type, count in behavior['message_types'].items():
        response += f"- {msg_type}: {count}\n"
    
    await update.message.reply_text(response) 