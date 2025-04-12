# Telegram Bot 管理面板

一个功能强大的 Telegram 机器人管理面板，提供群组管理、消息监控、用户行为分析等功能。

## 功能特点

- 群组管理
  - 群组活跃度监控
  - 用户行为分析
  - 敏感词检测
  - 关键词监控
- 用户管理
  - 用户验证
  - 积分系统
  - 警告系统
- 数据统计
  - 消息统计
  - 用户活跃度分析
  - 群组活跃度分析
- 文件管理
  - 多媒体文件存储
  - 文件分类管理
- Web 管理界面
  - 实时数据监控
  - 可视化数据展示
  - 多维度数据分析

## 技术栈

- Python 3.9
- SQLAlchemy
- Flask
- Docker
- Intel GPU 加速支持

## 安装说明

### 使用 Docker（推荐）

1. 拉取镜像：
```bash
docker pull your-dockerhub-username/tg-bot
```

2. 运行容器：
```bash
docker run -d \
  --name tg-bot \
  --gpus all \
  -v /vol1/1000/tg:/vol1/1000/tg \
  -p 5000:5000 \
  your-dockerhub-username/tg-bot
```

### 手动安装

1. 克隆仓库：
```bash
git clone https://github.com/your-username/tg-bot.git
cd tg-bot
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

4. 启动服务：
```bash
# 启动 Web UI
python webui/app.py

# 启动机器人
python main.py
```

## 配置说明

### 环境变量

- `TOKEN`: Telegram Bot Token
- `ADMIN_USER_IDS`: 管理员用户ID列表（逗号分隔）
- `DATABASE_URL`: 数据库连接URL
- `UPLOAD_FOLDER`: 文件上传目录

### 数据库

默认使用 SQLite 数据库，数据文件位于 `data/telegram_bot.db`。

## 使用说明

1. 访问 Web 管理界面：
   - 打开浏览器访问 `http://localhost:5000`
   - 使用管理员账号登录

2. 机器人命令：
   - `/start` - 开始使用机器人
   - `/help` - 显示帮助信息
   - `/checkin` - 每日签到
   - `/verify` - 开始真人验证
   - `/keywords` - 查看/设置监控关键词
   - `/stats` - 查看群组统计信息
   - `/monitor` - 查看监控设置
   - `/analysis` - 分析群组消息
   - `/visualize` - 生成数据可视化图表

## 开发说明

### 项目结构

```
tg-bot/
├── main.py              # 机器人主程序
├── models.py            # 数据库模型
├── utils.py             # 工具函数
├── webui/               # Web 管理界面
│   ├── app.py           # Web 应用主程序
│   └── templates/       # HTML 模板
├── data/                # 数据目录
└── requirements.txt     # 依赖列表
```

### 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目维护者：Your Name
- 邮箱：your.email@example.com 