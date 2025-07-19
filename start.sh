#!/bin/bash

# 执行初始化操作
init(){
    echo "执行初始化操作。"
    apt install gunicorn
    apt install python3.11
    apt install python3.11-venv
    python3.11 -m venv .venv
    source .venv/bin/activate
    .venv/bin/pip3 install --upgrade pip && .venv/bin/pip3 install -r requirements.txt
    echo "初始化完成。"
}
# 启动gunicorn服务
cd /srv/InterviewAssessment
source .venv/bin/activate
gunicorn --timeout 300 -w 1 -b 0.0.0.0:18888 app:app