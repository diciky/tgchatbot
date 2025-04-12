@echo off
echo 正在检查环境变量文件...
if not exist .env (
    echo 正在创建 .env 文件...
    copy .env.example .env
    echo 请编辑 .env 文件并设置必要的环境变量
    pause
    exit /b 1
)

echo 正在创建数据目录...
if not exist data (
    mkdir data
)

echo 正在设置环境变量...
set PYTHONPATH=%CD%

echo 正在安装依赖...
pip install -r requirements.txt

echo 正在启动机器人...
python main.py

pause 