#!/bin/bash

# 查找uvicorn中间件服务的进程ID
PID=$(ps -ef | grep "uvicorn middleware:app" | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "中间件服务未在运行。"
else
  echo "正在停止中间件服务 (PID: $PID)..."
  kill -9 $PID
  echo "中间件服务已停止。"
fi
