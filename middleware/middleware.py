import socketio
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import uuid

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "/tmp/uploaded_zips"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OS_IP_MAP = {
    "CentOS7": "192.168.200.100",
    "CentOS8": "192.168.200.101",
    "CentOS9": "192.168.200.102"
}

host = os.environ.get("UVICORN_HOST", "0.0.0.0")
port = os.environ.get("UVICORN_PORT", "8000")
print(f"[INFO] 中间件服务启动，监听 {host}:{port}")

BACKEND_PORT = os.environ.get("BACKEND_PORT", "5000")

# FastAPI原有路由
@fastapi_app.post("/build")
async def build(request: Request):
    data = await request.json()
    os_type = data.get("os")
    ip = OS_IP_MAP.get(os_type)
    print(f"[INFO] 收到前端构建请求: os={os_type}, 目标后端IP={ip}, data={data}")
    if not ip:
        print("[WARN] 未知系统类型，无法转发")
        return JSONResponse({"error": "未知系统"}, status_code=400)
    try:
        resp = requests.post(f"http://{ip}:{BACKEND_PORT}/build", json=data)
        print(f"[INFO] 已转发到后端，响应: {resp.status_code}")
        return JSONResponse(resp.json())
    except Exception as e:
        print(f"[ERROR] 转发到后端失败: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@fastapi_app.post("/upload_zip")
async def upload_zip(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    print(f"[INFO] 收到后端上传zip包: {filename}")
    return {"download_url": f"/download/{filename}"}

@fastapi_app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        print(f"[WARN] 下载请求文件不存在: {filename}")
        return JSONResponse({"error": "文件不存在"}, status_code=404)
    print(f"[INFO] 提供zip包下载: {filename}")
    return FileResponse(file_path, filename=filename)

# socket.io事件处理
@sio.event
async def connect(sid, environ):
    print(f"[INFO] 前端socket.io连接: {sid}")

@sio.event
async def disconnect(sid):
    print(f"[INFO] 前端socket.io断开: {sid}")

@sio.event
async def start_build(sid, data):
    os_type = data.get("os")
    ip = OS_IP_MAP.get(os_type)
    print(f"[INFO] 前端请求构建: os={os_type}, 目标后端IP={ip}, data={data}")
    if not ip:
        await sio.emit("log", {"log": "未知系统\n"}, room=sid)
        await sio.emit("done", {"zip_url": ""}, room=sid)
        return
    import socketio as sio_client
    backend_sio = sio_client.AsyncClient()
    try:
        await backend_sio.connect(f"http://{ip}:{BACKEND_PORT}", socketio_path="/socket.io/")
        print(f"[INFO] 已连接到后端socket.io: {ip}:{BACKEND_PORT}")
        await backend_sio.emit("start_build", data)
    except Exception as e:
        print(f"[ERROR] 连接后端socket.io失败: {e}")
        await sio.emit("log", {"log": f"后端连接失败: {e}\n"}, room=sid)
        await sio.emit("done", {"zip_url": ""}, room=sid)
        return

    @backend_sio.on("log")
    async def on_log(data2):
        await sio.emit("log", data2, room=sid)

    @backend_sio.on("done")
    async def on_done(data2):
        await sio.emit("done", data2, room=sid)
        print(f"[INFO] 构建完成，zip_url={data2.get('zip_url')}")
        await backend_sio.disconnect()

    # 保持连接直到后端断开
    try:
        while True:
            await backend_sio.sleep(1)
    except Exception as e:
        print(f"[WARN] 后端socket.io连接异常: {e}")

# 用ASGIApp包裹
app = socketio.ASGIApp(sio, fastapi_app) 
