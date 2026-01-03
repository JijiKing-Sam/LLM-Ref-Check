# 部署指南

## 本地部署

### 1. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/JijiKing-Sam/LLM-Ref-Check.git
cd LLM-Ref-Check

# 安装依赖
python -m pip install -r requirements.txt
```

### 2. 启动 Web 界面

```bash
# 方法1: 直接启动
streamlit run app.py

# 方法2: 使用启动脚本
bash run_web.sh

# 方法3: 指定端口和地址
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 3. 访问界面

打开浏览器访问: `http://localhost:8501`

## Streamlit Cloud 部署

### 1. 准备仓库

确保你的代码已推送到 GitHub 仓库。

### 2. 部署步骤

1. 访问 [Streamlit Cloud](https://streamlit.io/cloud)
2. 使用 GitHub 账号登录
3. 点击 "New app"
4. 选择你的仓库和分支
5. 设置主文件路径为 `app.py`
6. 点击 "Deploy"

### 3. 配置要求

- Python 版本: 3.8+
- 主文件: `app.py`
- 依赖文件: `requirements.txt`

## Docker 部署

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### 2. 构建和运行

```bash
# 构建镜像
docker build -t llm-ref-check .

# 运行容器
docker run -p 8501:8501 llm-ref-check
```

## 服务器部署

### 使用 systemd 服务

创建服务文件 `/etc/systemd/system/llm-ref-check.service`:

```ini
[Unit]
Description=LLM Ref Check Web Service
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/LLM-Ref-Check
Environment="PATH=/path/to/conda/envs/cirag0/bin"
ExecStart=/path/to/conda/envs/cirag0/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable llm-ref-check
sudo systemctl start llm-ref-check
```

### 使用 Nginx 反向代理

Nginx 配置示例:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## 环境变量配置

可以通过环境变量配置 Streamlit:

```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

## 性能优化

1. **启用缓存**: Streamlit 会自动缓存函数结果
2. **限制并发**: 在 `~/.streamlit/config.toml` 中配置:

```toml
[server]
maxUploadSize = 10
maxMessageSize = 10
```

3. **使用生产模式**: 设置 `STREAMLIT_SERVER_HEADLESS=true`

## 故障排查

### 端口被占用

```bash
# 检查端口占用
lsof -i :8501

# 使用其他端口
streamlit run app.py --server.port 8502
```

### 依赖问题

```bash
# 重新安装依赖
python -m pip install --upgrade -r requirements.txt
```

### 权限问题

```bash
# 确保脚本有执行权限
chmod +x run_web.sh
```
