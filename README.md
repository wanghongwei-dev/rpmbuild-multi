# RPM 包一键构建系统

## 项目简介
本项目为前后端分离的RPM包自助构建系统，采用三层分布式架构，支持多系统、多分支选择，实时日志推送，自动打包并提供下载，适合企业级RPM自动化构建场景。

<img width="794" height="416" alt="企业微信截图_1753153837666" src="https://github.com/user-attachments/assets/37659e43-cbdb-4cc2-afab-bfe16df9c4df" />

### 架构
- **前端（React+Vite）**: 纯粹的用户界面，由Nginx托管，所有请求均通过相对路径发出。
- **中间件（FastAPI）**: API网关，作为前端的唯一入口，负责业务路由、日志聚合和文件中转。
- **后端（Flask）**: 构建执行器，接收中间件指令，执行实际的RPM构建任务。

## 目录结构
```
rpmbuild/
├── frontend/                # 前端React项目
│   ├── src/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── middleware/              # 中间件FastAPI
│   ├── middleware.py
│   ├── requirements.txt
│   ├── startup.sh
│   └── shutdown.sh
├── server/                  # 后端Flask构建服务
│   ├── app.py
│   ├── requirements.txt
│   ├── rpmbuild.sh
│   ├── startup.sh
│   └── shutdown.sh
├── nginx/conf.d/nginx_rpmbuild.conf      # Nginx生产环境server配置示例（放到/etc/nginx/conf.d/）
├── LICENSE
└── README.md                # 项目说明
```

## 主要功能
- 前端页面选择系统、分支、输入包名，实时查看构建日志。
- 中间件根据系统类型，自动路由到不同的后端构建服务器。
- 后端负责实际构建、打包，并将产物（zip包）主动上传到中间件。
- 构建完成后自动提供zip包下载。

## 依赖安装

### 1. 后端依赖
```bash
cd server
pip install -r requirements.txt
```

### 2. 中间件依赖
```bash
cd middleware
pip install -r requirements.txt
```

### 3. 前端依赖
```bash
cd frontend
npm install
```

## 部署与启动（生产环境）

### 1. 打包前端
```bash
cd frontend
npm run build
```

### 2. 启动后端服务
```bash
cd server
bash startup.sh
```

### 3. 启动中间件服务
```bash
cd middleware
bash startup.sh
```

### 4. 配置并启动Nginx
1.  修改 `nginx_rpmbuild.conf` 文件，将 `root /path/to/frontend/dist;` 替换为实际路径。
2.  修改 `server_name` 为你自己的域名或服务器IP，**不能与其它server段冲突**。
3.  将 `nginx_rpmbuild.conf` 复制到 `/etc/nginx/conf.d/` 目录下。
4.  重载或启动Nginx服务: `systemctl reload nginx` 或 `systemctl start nginx`。

## 使用方法

1.  在浏览器访问Nginx监听的地址（如 http://your-domain.com 或 http://服务器IP）。
2.  在页面上选择目标系统、分支，输入软件包名或仓库地址。
3.  点击“开始构建”按钮，页面下方会实时显示构建日志。
4.  构建完成后，页面会出现“下载全部RPM包”按钮，点击即可下载zip包。

## 环境变量说明

### 中间件（middleware/startup.sh）
```
export UVICORN_HOST=0.0.0.0
export UVICORN_PORT=8000
export BACKEND_PORT=5000
```

### 后端（server/startup.sh）
```
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export MIDDLEWARE_HOST=中间件服务器IP或域名（本机可用127.0.0.1）
export MIDDLEWARE_PORT=8000
```

## 常见问题

- **端口冲突/防火墙**: 确保8000、5000端口对内网开放，Nginx监听端口（如80）对外开放。
- **Nginx 502错误**: 检查中间件服务是否正常运行。
- **zip包下载失败**: 检查中间件 `/tmp/uploaded_zips` 目录权限。
- **构建失败**: 查看后端日志（`server/app.log`）和rpmbuild.sh输出。
- **多后端支持**: 在 `middleware/middleware.py` 的 `OS_IP_MAP` 中配置更多后端服务器。

## 贡献与反馈
如有建议、bug或需求，欢迎提issue或联系维护者。

## 许可证
本项目采用Apache License 2.0，详见LICENSE文件。
