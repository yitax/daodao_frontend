# DaoDao智能记账助手 - 部署指南

## 1. 准备工作

- **云服务器**: 一台全新的Ubuntu 22.04服务器。
- **公网IP**: 确保您有服务器的公网IP地址。
- **防火墙/安全组**: 确保开放了以下端口：
  - **22** (用于SSH登录)
  - **80** (用于HTTP访问)

---

## 2. 服务器环境初始化

*这些命令只需在第一次配置服务器时运行。*

### 2.1. SSH登录服务器
```bash
# 将 user 替换为您的用户名，your_server_ip 替换为服务器IP
ssh user@your_server_ip
```

### 2.2. 更新系统并安装基础工具
```bash
# 更新软件包列表并升级
sudo apt update && sudo apt upgrade -y

# 安装Git, Nginx
sudo apt install -y git nginx
```

### 2.3. 安装 Docker 和 Docker Compose
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户添加到docker组，这样可以不用sudo执行docker命令
# 注意：执行后需要重新登录SSH才能生效！
sudo usermod -aG docker ${USER}

# 安装Docker Compose
sudo apt install -y docker-compose-v2
```
**重要提示**: 执行 `usermod` 命令后，请**断开SSH连接并重新登录**，以使用户组权限生效。

---

## 3. 部署应用

### 3.1. 克隆代码仓库
```bash
# 在用户主目录下克隆您的项目
# 将 <your-github-repo-url> 替换成您项目的GitHub仓库地址
git clone <your-github-repo-url> daodao

# 进入项目目录
cd daodao
```

### 3.2. 创建环境变量文件
这是部署中最关键的一步。
```bash
# 创建并编辑 .env 文件
nano .env
```
将以下内容**复制粘贴**到编辑器中。 **请务必替换成您自己的真实密钥**。

```env
# --- .env 文件内容 ---

# 替换为您的OpenAI API Key (或其他服务的API Key)
API_KEY=your_new_api_key_here

# 替换为您的新JWT签名密钥 (必须设置一个复杂的随机字符串)
SECRET_KEY=your_new_strong_and_random_secret_string

# --- 结束 ---
```
编辑完成后，按 `Ctrl+X`，然后按 `Y`，最后按 `Enter` 保存并退出。

### 3.3. 构建并启动应用容器
```bash
# 使用Docker Compose在后台构建并启动所有服务
docker-compose up --build -d
```

### 3.4. 验证容器运行状态
```bash
# 查看正在运行的容器
docker-compose ps
```
您应该能看到 `daodao-backend` 和 `daodao-frontend` 两个服务都处于 `up` 状态。

---

## 4. 配置Nginx反向代理 (HTTP)

*此步骤将您的应用通过公网IP的80端口暴露出去。*

### 4.1. 创建Nginx配置文件
```bash
# 为您的应用创建一个新的Nginx配置文件
sudo nano /etc/nginx/sites-available/daodao
```
将以下配置**完整复制并粘贴**到 `nano` 编辑器中。 **将 `your_server_ip` 替换成您的真实公网IP**。

```nginx
# /etc/nginx/sites-available/daodao

server {
    listen 80;
    server_name 47.98.122.118; # 这里填写您的服务器公网IP

    location / {
        # 将请求代理到前端容器
        # Docker Compose默认将前端容器暴露在8080端口
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        # 将API请求代理到后端容器
        # Docker Compose默认将后端容器暴露在8000端口
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
保存并退出 (`Ctrl+X`, `Y`, `Enter`)。

### 4.2. 启用Nginx配置
```bash
# 创建软链接以启用该站点配置
sudo ln -s /etc/nginx/sites-available/daodao /etc/nginx/sites-enabled/

# 移除默认的Nginx欢迎页面配置，防止冲突
sudo rm /etc/nginx/sites-enabled/default

# 测试Nginx配置是否有语法错误
sudo nginx -t
```
如果显示 `syntax is ok` 和 `test is successful`，则可以继续。

### 4.3. 重启Nginx使配置生效
```bash
sudo systemctl restart nginx
```

**部署完成！**

现在，您可以通过浏览器访问 `http://your_server_ip` (请替换成您的真实IP) 来使用您的应用了。

---

## 5. 日常维护

### 更新应用
```bash
cd ~/daodao && git pull && docker-compose up --build -d
```

### 查看日志
```bash
# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
``` 