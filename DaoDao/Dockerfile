# 使用官方Python 3.9 slim版本作为基础镜像
FROM python:3.9-slim

# 设置环境变量，防止Python写入.pyc文件
ENV PYTHONDONTWRITEBYTECODE 1
# 确保Python输出是无缓冲的
ENV PYTHONUNBUFFERED 1

# 设置工作目录
WORKDIR /app

# 更新pip
RUN pip install --upgrade pip

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
# --no-cache-dir: 不缓存包，减小镜像大小
# --compile: 编译依赖，提高启动速度
RUN pip install --no-cache-dir --compile -r requirements.txt

# 复制所有应用代码到工作目录
COPY . .

# 暴露容器的8000端口
EXPOSE 8000

# 启动应用的命令
# 使用4个worker进程来处理请求
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"] 