#!/bin/bash

# 查找Flask后端服务的进程ID
PID=$(ps -ef | grep "python3 -u app.py" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "后端服务未在运行。"
else
  echo "正在停止后端服务 (PID: $PID)..."
  kill -9 $PID
  echo "后端服务已停止。"
fi
