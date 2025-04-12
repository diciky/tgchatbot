import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from models import Session, User, Group, Message, Keyword, Alert, UserGroup
from analyzer import stats_command
from visualizer import visualize_command
from keyword_monitor import (
    add_sensitive_word_command,
    remove_sensitive_word_command,
    check_behavior_command,
    monitor
)
from monitor import check_group_activity, check_user_behavior_alert, GroupMonitor
from utils import generate_verification_code
from file_handler import get_file_info, save_file, update_message_with_file

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 获取环境变量
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# 处理管理员ID列表，移除注释和空格
admin_ids_str = os.getenv('ADMIN_USER_IDS', '')
if admin_ids_str:
    # 移除注释部分
    admin_ids_str = admin_ids_str.split('#')[0].strip()
    # 分割并转换为整数列表
    ADMIN_USER_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
else:
    ADMIN_USER_IDS = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/start命令"""
    await update.message.reply_text('欢迎使用群组管理机器人！\n'
                                  '我可以帮助您：\n'
                                  '1. 收集群组消息\n'
                                  '2. 监控关键词\n'
                                  '3. 真人验证\n'
                                  '4. 每日签到\n'
                                  '5. 消息转Telegraph\n'
                                  '6. 群组监控告警\n'
                                  '7. 消息统计分析\n'
                                  '使用 /help 查看详细命令')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理/help命令"""
    help_text = """
欢迎使用群组管理机器人！以下是可用命令：

/start - 开始使用机器人
/help - 显示此帮助信息
/checkin - 每日签到
/verify - 开始真人验证
/keywords - 查看/设置监控关键词
/stats - 查看群组统计信息
/monitor - 查看监控设置
/analysis - 分析群组消息
/visualize - 生成数据可视化图表

🔒 敏感词管理：
/addword <敏感词> - 添加敏感词
/removeword <敏感词> - 删除敏感词
/checkbehavior - 检查用户行为分析
    """
    await update.message.reply_text(help_text)

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理每日签到"""
    # TODO: 实现签到逻辑
    await update.message.reply_text("签到功能开发中...")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理真人验证"""
    # TODO: 实现验证逻辑
    await update.message.reply_text("验证功能开发中...")

async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理监控命令"""
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text("此命令只能在群组中使用！")
        return
    
    try:
        # 获取群组ID
        group_id = update.effective_chat.id
        
        # 获取数据库会话
        session = Session()
        try:
            # 获取群组
            group = session.query(Group).filter_by(telegram_id=group_id).first()
            if not group:
                await update.message.reply_text("群组未注册，请先发送一条消息！")
                return
            
            # 创建监控实例
            group_monitor = GroupMonitor()
            try:
                # 检查群组活跃度
                activity = group_monitor.check_message_activity(group.id)
                
                # 检查关键词告警
                alerts = group_monitor.check_keyword_alerts(group.id)
                
                # 构建响应消息
                response = (
                    f"📊 群组监控报告\n\n"
                    f"群组名称: {group.title}\n"
                    f"最近 {activity['time_period']} 小时活跃度:\n"
                    f"- 消息数量: {activity['message_count']}\n"
                    f"- 活跃用户数: {activity['active_users']}\n\n"
                )
                
                if alerts:
                    response += "⚠️ 关键词告警:\n"
                    for alert in alerts:
                        response += f"- {alert}\n"
                
                await update.message.reply_text(response)
                
            finally:
                group_monitor.close()
            
        except Exception as e:
            logger.error(f"获取监控数据失败: {e}")
            await update.message.reply_text("获取监控数据失败，请稍后重试！")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"处理监控命令失败: {e}")
        await update.message.reply_text("处理监控命令时发生错误！")

async def analysis_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理分析命令"""
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup', 'channel', 'private']:
        await update.message.reply_text("此命令只能在群组、频道或私聊中使用！")
        return
    
    await stats_command(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理所有消息"""
    # 获取数据库会话
    session = Session()
    try:
        message = update.message
        if not message:
            return

        # 获取或创建用户
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            session.add(user)
            session.commit()
        
        # 检查验证码
        if not user.is_verified and user.verification_code:
            if message.text == user.verification_code:
                user.is_verified = True
                user.verification_code = None
                session.commit()
                await update.message.reply_text("✅ 验证成功！您现在可以使用所有功能了。")
            else:
                await update.message.reply_text("❌ 验证码错误，请重试！")
                return
        
        # 如果是群组消息，获取或创建群组
        group = None
        if message.chat.type in ['group', 'supergroup']:
            group = session.query(Group).filter_by(telegram_id=message.chat.id).first()
            if not group:
                group = Group(
                    telegram_id=message.chat.id,
                    title=message.chat.title,
                    type=message.chat.type,
                    is_monitoring=True
                )
                session.add(group)
                session.commit()
            
            # 更新用户-群组关系
            if group and user:
                user_group = session.query(UserGroup).filter_by(
                    user_id=user.id,
                    group_id=group.id
                ).first()
                if not user_group:
                    user_group = UserGroup(
                        user_id=user.id,
                        group_id=group.id
                    )
                    session.add(user_group)
                    session.commit()
        
        # 创建消息记录
        msg = Message(
            message_id=message.message_id,
            user_id=user.id,
            group_id=group.id if group else None,
            content=message.text or '',  # 保存文本消息内容
            chat_type=message.chat.type
        )
        
        # 处理文件
        file_type, file_id, file_size, mime_type = get_file_info(update)
        if file_type and file_id:
            file_path = await save_file(update, context, file_type, file_id, group.id if group else None)
            if file_path:
                update_message_with_file(msg, file_type, file_id, file_path, file_size, mime_type)
        
        session.add(msg)
        session.commit()
        
        # 记录日志
        logger.info(f"保存消息: 用户={user.telegram_id}, 群组={group.telegram_id if group else None}, 类型={message.chat.type}")
        
        # 检查群组活跃度
        if message.chat.type in ['group', 'supergroup']:
            await check_group_activity(update, context)
        
        # 检查用户行为
        await check_user_behavior_alert(update, context)
        
        # 检查敏感词
        if message.text:
            sensitive_words = monitor.check_sensitive_content(message.text)
            if sensitive_words:
                await update.message.reply_text(
                    f"⚠️ 检测到敏感词使用！\n"
                    f"敏感词: {', '.join(sensitive_words)}"
                )
        
    except Exception as e:
        logger.error(f"处理消息时发生错误: {e}")
    finally:
        session.close()

async def add_sensitive_word_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """添加敏感词命令"""
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup', 'channel', 'private']:
        await update.message.reply_text("此命令只能在群组、频道或私聊中使用！")
        return
    
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
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup', 'channel', 'private']:
        await update.message.reply_text("此命令只能在群组、频道或私聊中使用！")
        return
    
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
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup', 'channel', 'private']:
        await update.message.reply_text("此命令只能在群组、频道或私聊中使用！")
        return
    
    user_id = update.effective_user.id
    group_id = update.effective_chat.id if chat_type != 'private' else None
    
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

async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理签到命令"""
    try:
        user_id = update.effective_user.id
        session = Session()
        
        try:
            # 获取用户
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                await update.message.reply_text("请先发送一条消息后再尝试签到！")
                return
            
            # 检查是否已经签到
            now = datetime.now()
            if user.last_checkin and user.last_checkin.date() == now.date():
                await update.message.reply_text("今天已经签到过了！")
                return
            
            # 更新签到信息
            user.last_checkin = now
            user.points += 10  # 每次签到获得10积分
            session.commit()
            
            await update.message.reply_text(
                f"✅ 签到成功！\n"
                f"获得积分: 10\n"
                f"当前积分: {user.points}"
            )
            
        except Exception as e:
            logger.error(f"处理签到失败: {e}")
            await update.message.reply_text("签到失败，请稍后重试！")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"处理签到命令失败: {e}")
        await update.message.reply_text("处理签到命令时发生错误！")

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理验证命令"""
    try:
        user_id = update.effective_user.id
        session = Session()
        
        try:
            # 获取用户
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                await update.message.reply_text("请先发送一条消息后再尝试验证！")
                return
            
            # 检查是否已经验证
            if user.is_verified:
                await update.message.reply_text("您已经通过验证了！")
                return
            
            # 生成验证码
            verification_code = generate_verification_code()
            
            # 保存验证码到用户记录
            user.verification_code = verification_code
            session.commit()
            
            await update.message.reply_text(
                f"🔐 验证码已生成\n"
                f"请在5分钟内输入以下验证码：\n"
                f"`{verification_code}`\n\n"
                f"注意：验证码区分大小写！",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"处理验证失败: {e}")
            await update.message.reply_text("验证失败，请稍后重试！")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"处理验证命令失败: {e}")
        await update.message.reply_text("处理验证命令时发生错误！")

async def keywords_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理关键词命令"""
    chat_type = update.effective_chat.type
    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text("此命令只能在群组中使用！")
        return
    
    try:
        # 获取群组ID
        group_id = update.effective_chat.id
        
        # 获取数据库会话
        session = Session()
        try:
            # 获取群组
            group = session.query(Group).filter_by(telegram_id=group_id).first()
            if not group:
                await update.message.reply_text("群组未注册，请先发送一条消息！")
                return
            
            # 获取群组的关键词列表
            keywords = session.query(Keyword).filter_by(group_id=group.id).all()
            
            if not keywords:
                await update.message.reply_text("当前没有设置任何关键词。\n\n使用 /addword 添加关键词")
                return
            
            # 构建响应消息
            response = "📝 当前监控的关键词列表：\n\n"
            for keyword in keywords:
                response += f"- {keyword.word}\n"
            
            response += "\n使用 /addword 添加关键词\n使用 /removeword 删除关键词"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"获取关键词列表失败: {e}")
            await update.message.reply_text("获取关键词列表失败，请稍后重试！")
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"处理关键词命令失败: {e}")
        await update.message.reply_text("处理关键词命令时发生错误！")

def main() -> None:
    """启动机器人"""
    # 创建应用
    application = Application.builder().token(TOKEN).build()
    
    # 添加命令处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("checkin", checkin_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("keywords", keywords_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("monitor", monitor_command))
    application.add_handler(CommandHandler("analysis", analysis_command))
    application.add_handler(CommandHandler("visualize", visualize_command))
    application.add_handler(CommandHandler("addword", add_sensitive_word_command))
    application.add_handler(CommandHandler("removeword", remove_sensitive_word_command))
    application.add_handler(CommandHandler("checkbehavior", check_behavior_command))
    
    # 添加通用消息处理器（必须放在最后）
    application.add_handler(MessageHandler(filters.ALL, handle_message))
    
    # 启动机器人
    application.run_polling()

if __name__ == '__main__':
    main() 