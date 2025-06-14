# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 设置环境变量，当在服务器上部署时使用正确的基础路径
# 这个URL应该替换为实际部署的URL或相对路径
ENV VITE_API_BASE_URL=''
ENV NODE_ENV=production

COPY package*.json ./
RUN npm ci

COPY . .
RUN chmod +x node_modules/.bin/vite 
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 确保Nginx可以处理SPA应用的路由
RUN echo "    location / { \
        try_files \$uri \$uri/ /index.html; \
    }" > /etc/nginx/conf.d/default.conf.append \
    && sed -i '/location \/ {/r /etc/nginx/conf.d/default.conf.append' /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 