# DaoDao智能记账助手 - 云服务器部署终极指南

## 1. 准备工作

### 1.1. 云服务器
- **要求**: 一台全新的云服务器 (例如: 阿里云, 腾讯云, AWS, DigitalOcean)。
- **操作系统**: **Ubuntu 22.04 LTS** (推荐)。
- **配置**: 至少 1核CPU / 1GB RAM / 25GB SSD。
- **网络**: 拥有公网IP，并确保防火墙/安全组开放了以下端口：
  - **22** (用于SSH登录)
  - **80** (用于HTTP)
  - **443** (用于HTTPS)

### 1.2. 域名
- 准备一个域名，并将其解析到您的服务器公网IP。这对于配置HTTPS至关重要。

---

## 2. 服务器环境初始化 (在服务器上执行)

*这些命令只需在第一次配置服务器时运行。*

### 2.1. 使用SSH登录服务器
```bash
# 将 user 替换为您的用户名，your_server_ip 替换为服务器IP
ssh user@your_server_ip
```

### 2.2. 更新系统并安装基础工具
```bash
# 更新软件包列表
sudo apt update && sudo apt upgrade -y

# 安装Git, Nginx, 和 Certbot (用于HTTPS)
sudo apt install -y git nginx certbot python3-certbot-nginx
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

## 3. 部署应用 (在服务器上执行)

### 3.1. 克隆代码仓库
```bash
# 在用户主目录下克隆您的项目
# 将 <your-github-repo-url> 替换成您项目的GitHub仓库地址
git clone <your-github-repo-url> daodao

# 进入项目目录
cd daodao
```

### 3.2. 创建环境变量文件
这是部署中最关键的一步。`docker-compose` 会自动加载这个文件中的配置。
```bash
# 创建并编辑 .env 文件
nano .env
```
将以下内容**复制粘贴**到 `nano` 编辑器中。 **请务必替换成您自己的真实密钥**。

```env
# --- .env 文件内容 ---

# OpenAI API 配置
# 替换为您的OpenAI API Key
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# JWT 签名密钥 (必须设置一个复杂的随机字符串，用于用户认证)
# 您可以使用 `openssl rand -hex 32` 命令生成一个
SECRET_KEY=a_very_strong_and_long_random_secret_string_for_production

# --- 结束 ---
```
编辑完成后，按 `Ctrl+X`，然后按 `Y`，最后按 `Enter` 保存并退出。

### 3.3. 构建并启动应用容器
```bash
# 使用Docker Compose在后台构建并启动所有服务
docker-compose up --build -d
```
- `--build`: 强制重新构建镜像，确保使用最新的代码。
- `-d`: 在后台（detached模式）运行容器。

### 3.4. 验证容器运行状态
```bash
# 查看正在运行的容器
docker-compose ps
```
您应该能看到 `daodao-backend` 和 `daodao-frontend` 两个服务都处于 `running` 或 `up` 状态。如果不是，请使用 `docker-compose logs backend` 或 `docker-compose logs frontend` 查看日志排查问题。

---

## 4. 配置Nginx反向代理和HTTPS (在服务器上执行)

*此步骤将您的应用暴露到公网，并通过域名和SSL证书进行保护。*

### 4.1. 创建Nginx配置文件
```bash
# 为您的应用创建一个新的Nginx配置文件
# 将 your-domain.com 替换为您的真实域名
sudo nano /etc/nginx/sites-available/your-domain.com
```
将以下配置**完整复制并粘贴**到 `nano` 编辑器中。 **请务必将 `your-domain.com` 替换成您的真实域名** (共4处)。

```nginx
# /etc/nginx/sites-available/your-domain.com

# HTTP请求将自动重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

# HTTPS服务配置
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL证书路径将在下一步由Certbot自动配置
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 推荐的SSL安全配置
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        # 将请求代理到前端容器
        # Docker Compose默认将前端容器暴露在80端口
        proxy_pass http://localhost:80;
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
# 将 your-domain.com 替换为您的真实域名
sudo ln -s /etc/nginx/sites-available/your-domain.com /etc/nginx/sites-enabled/

# 测试Nginx配置是否有语法错误
sudo nginx -t
```
如果显示 `syntax is ok` 和 `test is successful`，则可以继续。

### 4.3. 获取SSL证书并自动配置Nginx
```bash
# 使用Certbot为您的域名申请SSL证书，并让它自动更新Nginx配置
# 将 your-domain.com 替换为您的真实域名
sudo certbot --nginx -d your-domain.com
```
- 按照提示输入您的邮箱地址，同意服务条款。
- Certbot会自动完成验证，获取证书，并修改您的Nginx配置文件来启用HTTPS。

### 4.4. 重启Nginx使配置生效
```bash
sudo systemctl restart nginx
```

**恭喜！** 现在您可以通过 `https://your-domain.com` 访问您的应用了。

---

## 5. 日常维护

### 更新应用
当您在GitHub上更新了代码后，登录服务器执行以下命令即可更新部署：
```bash
# 进入项目目录
cd ~/daodao

# 拉取最新的代码
git pull

# 重新构建并以分离模式启动容器
docker-compose up --build -d
```

### 查看日志
```bash
# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```
按 `Ctrl+C` 停止查看。

### 停止/启动服务
```bash
# 停止所有服务
docker-compose down

# 仅停止服务（不删除容器）
docker-compose stop

# 启动已停止的服务
docker-compose start
``` 