 
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 设置工作目录
WORKDIR /app

# 更新pip
# RUN pip install --upgrade pip
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
# RUN pip install --no-cache-dir --compile -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 复制所有应用代码到工作目录
COPY . .

# 暴露容器的8000端口
EXPOSE 8000

# 启动应用的命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]