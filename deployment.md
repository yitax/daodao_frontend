# DaoDao 智能记账助手部署计划

## 1. 项目概述

DaoDao智能记账助手是一个前后端分离的应用：
- 后端：基于FastAPI的Python应用
- 前端：基于Vue.js的SPA应用
- 数据库：SQLite (生产环境可考虑升级为PostgreSQL)

## 2. 部署架构

```
                           ┌───────────────┐
                           │    Nginx      │
                           │ 反向代理/HTTPS │
                           └───────┬───────┘
                                   │
                 ┌─────────────────┴────────────────┐
                 │                                  │
         ┌───────┴──────┐                  ┌────────┴───────┐
         │ 前端容器      │                  │ 后端容器        │
         │ (Vue.js/Nginx)│                  │ (FastAPI/Uvicorn)│
         └───────┬──────┘                  └────────┬───────┘
                 │                                  │
                 │                          ┌───────┴───────┐
                 │                          │               │
                 │                          │  SQLite数据库  │
                 │                          │  (持久化卷)    │
                 │                          │               │
                 │                          └───────────────┘
                 │
        ┌────────┴────────┐
        │静态资源(HTML/CSS/JS)│
        └─────────────────┘
```

## 3. 环境要求

### 服务器要求
- 操作系统：Ubuntu 20.04 LTS 或更高版本
- CPU：至少2核
- 内存：至少2GB RAM
- 存储：至少20GB SSD
- 网络：公网IP，开放80和443端口

### 软件要求
- Docker: 20.10.x 或更高
- Docker Compose: v2.x
- Nginx (主机上，用于HTTPS和反向代理)
- Git

## 4. Docker配置文件

### 后端Dockerfile (backend/Dockerfile)
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端Dockerfile (frontend/Dockerfile)
```dockerfile
# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 前端Nginx配置 (frontend/nginx.conf)
```
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # 前端路由处理
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Compose (docker-compose.yml)
```yaml
version: '3'

services:
  backend:
    build: ./DaoDao
    container_name: daodao-backend
    restart: always
    environment:
      - DATABASE_URL=sqlite:///data/daodao.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    container_name: daodao-frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend
```

## 5. 部署流程

### 5.1 准备工作

1. **服务器初始化**
   ```bash
   # 更新系统
   sudo apt update && sudo apt upgrade -y
   
   # 安装必要工具
   sudo apt install -y git curl wget nano
   ```

2. **安装Docker和Docker Compose**
   ```bash
   # 安装Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # 安装Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   
   # 验证安装
   docker --version
   docker-compose --version
   ```

3. **创建部署目录**
   ```bash
   sudo mkdir -p /opt/daodao
   sudo chown $USER:$USER /opt/daodao
   ```

### 5.2 代码部署

1. **克隆代码**
   ```bash
   cd /opt/daodao
   git clone [项目Git仓库URL] .
   ```

2. **创建环境变量文件**
   ```bash
   cat > .env << EOF
   OPENAI_API_KEY=你的OpenAI_API_KEY
   EOF
   ```

3. **创建数据目录**
   ```bash
   mkdir -p /opt/daodao/data
   ```

### 5.3 容器构建与运行

1. **构建和启动容器**
   ```bash
   cd /opt/daodao
   docker-compose build
   docker-compose up -d
   ```

2. **验证服务**
   ```bash
   # 检查容器状态
   docker ps
   
   # 检查后端日志
   docker logs daodao-backend
   
   # 检查前端可访问性
   curl http://localhost
   
   # 检查API可访问性
   curl http://localhost:8000
   ```

### 5.4 配置HTTPS与域名 (可选)

1. **安装Nginx**
   ```bash
   sudo apt install -y nginx
   ```

2. **安装Certbot**
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   ```

3. **配置域名**
   ```bash
   sudo nano /etc/nginx/sites-available/daodao
   ```
   
   添加如下配置:
   ```
   server {
       listen 80;
       server_name your-domain.com;
       return 301 https://$host$request_uri;
   }
   
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
       
       location / {
           proxy_pass http://localhost:80;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /api/ {
           proxy_pass http://localhost:8000/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **启用站点配置**
   ```bash
   sudo ln -s /etc/nginx/sites-available/daodao /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **申请SSL证书**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

## 6. 运维管理

### 6.1 日常维护

1. **监控容器状态**
   ```bash
   docker stats
   ```

2. **查看应用日志**
   ```bash
   # 后端日志
   docker logs -f daodao-backend
   
   # 前端日志
   docker logs -f daodao-frontend
   ```

3. **重启服务**
   ```bash
   cd /opt/daodao
   docker-compose restart
   ```

### 6.2 更新部署

1. **拉取最新代码**
   ```bash
   cd /opt/daodao
   git pull
   ```

2. **重建并重启容器**
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

### 6.3 数据备份

1. **设置定时备份**
   ```bash
   # 创建备份脚本
   cat > /opt/daodao/backup.sh << 'EOF'
   #!/bin/bash
   
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/opt/backups/daodao"
   
   mkdir -p $BACKUP_DIR
   
   # 备份数据库
   cp /opt/daodao/data/daodao.db $BACKUP_DIR/daodao_$TIMESTAMP.db
   
   # 保留最近30天备份
   find $BACKUP_DIR -name "daodao_*.db" -type f -mtime +30 -delete
   EOF
   
   chmod +x /opt/daodao/backup.sh
   ```

2. **配置定时任务**
   ```bash
   echo "0 2 * * * /opt/daodao/backup.sh" | sudo tee -a /etc/crontab
   ```

### 6.4 性能优化

1. **调整Uvicorn工作进程**
   
   编辑docker-compose.yml:
   ```yaml
   backend:
     # ... 其他配置 ...
     command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

2. **配置Nginx缓存** (在主机Nginx配置中)
   ```
   # 在server块中添加
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
       expires 30d;
       add_header Cache-Control "public, no-transform";
   }
   ```

## 7. 故障排除

### 7.1 常见问题

1. **容器无法启动**
   ```bash
   # 检查错误日志
   docker logs daodao-backend
   
   # 检查配置文件
   cat /opt/daodao/.env
   ```

2. **数据库连接错误**
   ```bash
   # 检查数据库文件权限
   ls -la /opt/daodao/data
   
   # 修复权限
   sudo chown -R 1000:1000 /opt/daodao/data
   ```

3. **前端无法访问API**
   ```bash
   # 检查网络连接
   docker network inspect daodao_default
   
   # 检查Nginx配置
   docker exec -it daodao-frontend cat /etc/nginx/conf.d/default.conf
   ```

### 7.2 恢复流程

1. **从备份恢复数据**
   ```bash
   # 停止服务
   cd /opt/daodao
   docker-compose down
   
   # 恢复数据库
   cp /opt/backups/daodao/[备份文件名] /opt/daodao/data/daodao.db
   
   # 重启服务
   docker-compose up -d
   ```

## 8. 安全考量

1. **更新环境变量管理**
   - 将敏感信息从.env移至Docker Secrets或云服务提供商的密钥管理服务

2. **强化Nginx安全配置**
   ```
   # 添加安全相关头信息
   add_header X-Frame-Options "SAMEORIGIN";
   add_header X-XSS-Protection "1; mode=block";
   add_header X-Content-Type-Options "nosniff";
   add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';";
   ```

3. **定期更新依赖和容器镜像**
   ```bash
   # 更新依赖
   cd /opt/daodao/DaoDao
   pip install -U -r requirements.txt > requirements.txt
   
   # 更新前端依赖
   cd /opt/daodao/frontend
   npm update
   
   # 重建容器
   cd /opt/daodao
   docker-compose build --no-cache
   docker-compose up -d
   ```

## 9. 扩展性规划

### 9.1 迁移到PostgreSQL (推荐用于生产环境)

1. **更新docker-compose.yml增加数据库服务**
   ```yaml
   services:
     # ... 其他服务 ...
     
     postgres:
       image: postgres:15
       container_name: daodao-postgres
       restart: always
       environment:
         - POSTGRES_USER=daodao
         - POSTGRES_PASSWORD=${DB_PASSWORD}
         - POSTGRES_DB=daodao
       volumes:
         - postgres_data:/var/lib/postgresql/data
       ports:
         - "5432:5432"
   
   volumes:
     postgres_data:
   ```

2. **更新后端环境变量**
   ```
   DATABASE_URL=postgresql://daodao:${DB_PASSWORD}@postgres/daodao
   ```

### 9.2 水平扩展

可通过如下方式实现水平扩展:

1. **使用Docker Swarm或Kubernetes**
   - 将单机部署迁移至容器编排平台
   - 使用负载均衡器分发请求至多个后端实例

2. **使用云服务**
   - 考虑使用AWS ECS、Azure AKS或Google Cloud Run等服务
   - 配置自动扩缩容根据负载调整实例数量

## 10. 上线检查清单

- [ ] 确认所有环境变量正确配置
- [ ] 验证数据库持久化存储配置
- [ ] 测试API接口功能
- [ ] 检查前端页面加载和功能
- [ ] 确认HTTPS配置和证书有效性
- [ ] 验证备份脚本有效性
- [ ] 监控系统CPU、内存使用情况
- [ ] 检查系统日志中是否有错误
- [ ] 执行简单负载测试确认系统稳定性
- [ ] 更新防火墙规则，只开放必要端口 