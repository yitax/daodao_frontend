# 叨叨记账 

叨叨记账是一个智能AI记账助手，支持通过自然语言对话方式记录收支、查询财务报表，并提供多种AI性格选择。

## 项目架构

- 前端: Vue 3 + Element Plus
- 后端: Python + FastAPI + SQLAlchemy
- 数据库: SQLite 
- AI功能: OpenAI API

## 功能特点

- 自然语言记账: 通过对话形式完成日常记账
- 多种AI性格: 支持切换不同AI对话风格
- 智能信息提取: 自动从对话中提取收支信息,支持图片识别
- 分类自动推荐: 根据交易描述智能匹配分类
- 多维度财务报表: 支持多种图表展示财务状况
- 多层级账单查看: 年-月-日层级浏览账单
- 智能分析消费习惯：根据消费习惯给出建议 

## 项目结构

```
daodao/
├── backend/               # Python FastAPI后端
│   ├── app/               # 应用代码
│   │   ├── models/        # 数据模型
│   │   ├── routers/       # API路由
│   │   ├── services/      # 业务逻辑服务
│   │   ├── utils/         # 工具函数
│   │   └── main.py        # 应用入口
│   └── requirements.txt   # Python依赖
│
└── frontend/              # Vue前端
    ├── src/
    │   ├── assets/        # 静态资源
    │   ├── components/    # 通用组件
    │   ├── router/        # 路由配置
    │   ├── store/         # 状态管理
    │   ├── views/         # 页面组件
    │   ├── App.vue        # 根组件
    │   └── main.js        # 入口文件
    └── package.json       # 依赖配置
```

## 环境配置

### 后端环境变量

创建 `backend/.env` 文件:

```
# 数据库配置
DATABASE_URL=sqlite:///./daodao.db
# 可选：使用PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost/daodao

# JWT密钥，生产环境请使用强随机值
SECRET_KEY=your-secret-key-for-development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### 前端环境变量

创建 `frontend/.env` 文件:

```
# API基础URL
VITE_API_BASE_URL=http://localhost:8000/api

# 标题配置
VITE_APP_TITLE=叨叨记账
```

## 本地开发

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### 前端详细说明

#### 前提条件

- 安装 [Node.js](https://nodejs.org/) (推荐版本 16.x 或更高)
- 安装 [npm](https://www.npmjs.com/) (通常随Node.js一起安装)

#### 启动步骤

1. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **启动开发服务器**
   ```bash
   npm run dev
   ```
   成功启动后，终端会显示类似以下信息：
   ```
   VITE v4.5.0 ready in XXXms
   
   ➜  Local:   http://localhost:5173/
   ➜  Network: http://xxx.xxx.xxx.xxx:5173/
   ```
   
3. **访问应用**
   - 打开浏览器，访问 http://localhost:5173
   - 确保后端API服务已在运行中 (http://localhost:8000)

#### 常用命令

- **开发模式**
  ```bash
  npm run dev
  ```

- **构建生产版本**
  ```bash
  npm run build
  ```
  构建后的文件将位于 `dist` 目录

- **预览生产构建**
  ```bash
  npm run preview
  ```
  
- **代码检查**
  ```bash
  npm run lint
  ```

#### 故障排除

如遇到前端无法连接后端API的问题：
1. 确认后端服务已启动且运行在正确端口(默认8000)
2. 检查前端环境变量(VITE_API_BASE_URL)是否正确配置
3. 检查浏览器控制台是否有CORS(跨域)相关错误
4. 确认浏览器网络请求中有正确的授权头(Bearer Token)

#### 自定义配置

如需修改前端配置(如端口、代理设置等)，可编辑 `vite.config.js` 文件。
 
## 接口文档

启动后端后，可访问 `http://localhost:8000/docs` 查看API文档。

## 核心流程

1. 用户在聊天界面输入自然语言文本（如"昨天在商场买了一件衣服，花了300元"）
2. 系统使用LLM识别记账意图并提取关键财务信息（交易类型、金额、日期等）
3. 系统请求用户确认提取的信息，并支持修改
4. 确认后，信息被保存到数据库
5. 用户可通过多种报表查看、分析财务数据
6. 聊天界面默认只显示最近的10条消息记录，当用户上拉聊天记录时，系统会加载更早的消息，直到所有历史消息加载完毕
