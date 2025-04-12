from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import Session, User, Group, Message, Keyword, Alert
from datetime import datetime, timedelta
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 配置
UPLOAD_FOLDER = '/vol1/1000/tg'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        session = Session()
        user = session.query(User).filter_by(username=username).first()
        session.close()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': '用户名或密码错误'})
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/stats')
@login_required
def get_stats():
    session = Session()
    try:
        # 获取基本统计信息
        total_users = session.query(User).count()
        total_groups = session.query(Group).count()
        total_messages = session.query(Message).count()
        
        # 获取最近24小时的消息统计
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_messages = session.query(Message).filter(Message.created_at >= last_24h).count()
        
        # 获取活跃群组（最近24小时有消息的群组）
        active_groups = session.query(Group).join(Message).filter(
            Message.created_at >= last_24h
        ).distinct().count()
        
        return jsonify({
            'total_users': total_users,
            'total_groups': total_groups,
            'total_messages': total_messages,
            'recent_messages': recent_messages,
            'active_groups': active_groups
        })
    finally:
        session.close()

@app.route('/api/messages')
@login_required
def get_messages():
    session = Session()
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        messages = session.query(Message).order_by(Message.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        result = []
        for msg in messages:
            result.append({
                'id': msg.id,
                'content': msg.content,
                'file_type': msg.file_type,
                'file_path': msg.file_path,
                'created_at': msg.created_at.isoformat(),
                'user': {
                    'id': msg.user.telegram_id,
                    'username': msg.user.username,
                    'first_name': msg.user.first_name
                },
                'group': {
                    'id': msg.group.telegram_id if msg.group else None,
                    'title': msg.group.title if msg.group else None
                }
            })
        
        return jsonify(result)
    finally:
        session.close()

@app.route('/api/groups')
@login_required
def get_groups():
    session = Session()
    try:
        groups = session.query(Group).all()
        result = []
        for group in groups:
            result.append({
                'id': group.id,
                'telegram_id': group.telegram_id,
                'title': group.title,
                'type': group.type,
                'is_monitoring': group.is_monitoring,
                'message_count': len(group.messages),
                'user_count': len(group.users)
            })
        return jsonify(result)
    finally:
        session.close()

@app.route('/api/users')
@login_required
def get_users():
    session = Session()
    try:
        users = session.query(User).all()
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'is_admin': user.is_admin,
                'is_verified': user.is_verified,
                'points': user.points,
                'warning_count': user.warning_count
            })
        return jsonify(result)
    finally:
        session.close()

@app.route('/api/keywords')
@login_required
def get_keywords():
    session = Session()
    try:
        keywords = session.query(Keyword).all()
        result = []
        for keyword in keywords:
            result.append({
                'id': keyword.id,
                'word': keyword.word,
                'group_id': keyword.group_id,
                'severity': keyword.severity,
                'is_active': keyword.is_active
            })
        return jsonify(result)
    finally:
        session.close()

@app.route('/api/alerts')
@login_required
def get_alerts():
    session = Session()
    try:
        alerts = session.query(Alert).order_by(Alert.created_at.desc()).all()
        result = []
        for alert in alerts:
            result.append({
                'id': alert.id,
                'group_id': alert.group_id,
                'user_id': alert.user_id,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'severity': alert.severity,
                'is_resolved': alert.is_resolved,
                'created_at': alert.created_at.isoformat()
            })
        return jsonify(result)
    finally:
        session.close()

@app.route('/api/files/<path:filename>')
@login_required
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 