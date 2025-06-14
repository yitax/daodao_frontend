# 构建阶段
FROM node:18-alpine AS build-stage

WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production

# 先只复制package.json进行依赖安装
COPY package*.json ./
RUN npm install

# 复制所有源代码
COPY . .

# 添加vite命令执行权限
RUN chmod +x node_modules/.bin/vite

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine AS production-stage

# 从构建阶段复制构建结果到nginx目录
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 确保Nginx可以处理SPA路由
RUN echo "    location / { \
        try_files \$uri \$uri/ /index.html; \
    }" > /etc/nginx/extra.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 