# 构建阶段
FROM node:18-alpine as build-stage

WORKDIR /app

# 设置环境变量
ENV VITE_API_BASE_URL=''

COPY package*.json ./
RUN npm ci

COPY . .
RUN chmod +x node_modules/.bin/vite 
RUN npm run build

# 生产阶段
FROM nginx:stable-alpine as production-stage

COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 