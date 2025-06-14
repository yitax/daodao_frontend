# 构建阶段
FROM node:18-alpine AS build-stage

WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production

# 先复制package.json和package-lock.json
COPY package*.json ./

# 清理node_modules并全新安装依赖
RUN npm install

# 复制源代码
COPY . .

# 安装vite (确保它存在)
RUN npm install --save-dev vite @vitejs/plugin-vue

# 构建应用 (使用npx确保找到正确的vite路径)
RUN npx vite build

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