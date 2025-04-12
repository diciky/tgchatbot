#!/bin/bash

# 检查环境变量文件是否存在
if [ ! -f .env ]; then
    echo "正在创建 .env 文件..."
    cp .env.example .env
    echo "请编辑 .env 文件并设置必要的环境变量"
    exit 1
fi

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt

# 启动机器人
echo "正在启动机器人..."
python main.py 