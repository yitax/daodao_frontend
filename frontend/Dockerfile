# 构建阶段
FROM node:18-alpine AS build-stage

WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production

# 先复制package.json和package-lock.json
COPY package*.json ./

# 清理node_modules并全新安装依赖
RUN rm -rf node_modules && npm cache clean --force && npm install

# 复制源代码（不包括node_modules）
COPY . .

# 确保node_modules不会被覆盖（如果有的话）
RUN rm -rf node_modules && npm install

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