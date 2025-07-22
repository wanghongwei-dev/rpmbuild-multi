import os
import subprocess
import threading
import shutil
import time
import eventlet

eventlet.monkey_patch()

from flask import Flask, request, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/")
socketio = SocketIO(app, cors_allowed_origins="*")

RPMBUILD_RPMS = os.path.expanduser("~/rpmbuild/RPMS")
ZIP_OUTPUT_DIR = os.path.expanduser("/tmp/ZIPPKGS")
os.makedirs(ZIP_OUTPUT_DIR, exist_ok=True)

# 服务器地址
FLASK_HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
MIDDLEWARE_HOST = os.environ.get("MIDDLEWARE_HOST", "127.0.0.1")
MIDDLEWARE_PORT = os.environ.get("MIDDLEWARE_PORT", "8000")

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/download_zip/<path:filename>")
def download_zip(filename):
    print(f"[INFO] 下载请求: {filename}")
    return send_from_directory(ZIP_OUTPUT_DIR, filename, as_attachment=True)

@socketio.on("start_build")
def handle_build(data):
    repo_url = data.get("repo_url")
    branch = data.get("branch")
    sid = request.sid

    print(f"[INFO] 收到构建请求: repo_url={repo_url}, branch={branch}, sid={sid}")

    if not repo_url or not branch:
        print("[WARN] 参数错误")
        socketio.emit("log", {"log": "参数错误\n"}, room=sid)
        return

    def run_build(sid):
        written_files = []
        cmd = ["bash", "rpmbuild.sh", repo_url, branch]
        print(f"[INFO] 启动构建进程: {' '.join(cmd)}")
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in iter(proc.stdout.readline, ''):
                socketio.emit("log", {"log": line}, room=sid)
                rpm_path = None
                if "已写至：" in line:
                    rpm_path = line.split("已写至：", 1)[1].strip()
                elif "Wrote:" in line:
                    rpm_path = line.split("Wrote:", 1)[1].strip()
                if rpm_path and os.path.isfile(rpm_path):
                    written_files.append(rpm_path)
            proc.wait()
        except Exception as e:
            print(f"[ERROR] 构建进程异常: {e}")
            socketio.emit("log", {"log": f"[构建异常]{e}\n"}, room=sid)
            socketio.emit("done", {"zip_url": ""}, room=sid)
            return

        if written_files:
            written_files.sort(key=lambda x: os.path.getmtime(x))
            pkg_name = repo_url.strip().split('/')[-1].replace('.git','') if '/' in repo_url else repo_url.strip()
            timestamp = int(time.time())
            zip_name = f"{pkg_name}_{timestamp}.zip"
            zip_path = os.path.join(ZIP_OUTPUT_DIR, zip_name)
            import zipfile
            try:
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for f in written_files:
                        arcname = os.path.relpath(f, RPMBUILD_RPMS)
                        zipf.write(f, arcname)
                print(f"[INFO] 打包完成: {zip_path}")
            except Exception as e:
                print(f"[ERROR] 打包异常: {e}")
                socketio.emit("log", {"log": f"[打包异常]{e}\n"}, room=sid)
                socketio.emit("done", {"zip_url": ""}, room=sid)
                return

            # 上传zip包到中间件服务器
            try:
                import requests
                with open(zip_path, "rb") as f:
                    files = {"file": (zip_name, f, "application/zip")}
                    resp = requests.post(f"http://{MIDDLEWARE_HOST}:{MIDDLEWARE_PORT}/upload_zip", files=files)
                if resp.ok and resp.json().get("download_url"):
                    download_url = resp.json()["download_url"]
                    print(f"[INFO] zip包已上传到中间件服务器: {download_url}")
                else:
                    download_url = f"/download_zip/{zip_name}"
                    print(f"[WARN] zip包上传中间件服务器失败，使用本地下载: {download_url}")
            except Exception as e:
                print(f"[ERROR] 上传中间件服务器失败: {e}")
                socketio.emit("log", {"log": f"[上传中间件服务器失败]{e}\n"}, room=sid)
                download_url = f"/download_zip/{zip_name}"
            socketio.emit("done", {"zip_url": download_url}, room=sid)
        else:
            print("[WARN] 未找到RPM包")
            socketio.emit("log", {"log": f"[未找到RPM包]\n"}, room=sid)
            socketio.emit("done", {"zip_url": ""}, room=sid)

    threading.Thread(target=run_build, args=(sid,)).start()

if __name__ == "__main__":
    print(f"[INFO] 后端服务启动，监听 {FLASK_HOST}:{FLASK_PORT}，中间件地址: {MIDDLEWARE_HOST}:{MIDDLEWARE_PORT}")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT)
