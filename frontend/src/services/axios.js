import axios from 'axios';

// 创建axios实例
const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '',
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
    // 不设置默认超时
    timeout: 0
});

// 标记，防止多个请求同时触发token刷新
let isRefreshing = false;
let failedQueue = [];

// 处理被拦截的请求
const processQueue = (error, token = null) => {
    failedQueue.forEach(prom => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });

    failedQueue = [];
};

// 请求拦截器
axiosInstance.interceptors.request.use(
    config => {
        console.log(`[axios] 发送请求: ${config.method?.toUpperCase()} ${config.url}`);

        // 添加时间戳，防止缓存
        if (config.method?.toLowerCase() === 'get') {
            config.params = {
                ...config.params,
                _t: Date.now()
            }
        }

        // 优先使用会话存储的token，其次使用本地存储的token
        const sessionToken = sessionStorage.getItem('token');
        const localToken = localStorage.getItem('token');
        const token = sessionToken || localToken;

        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
            // 确保两个存储都有token，防止刷新后丢失
            if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
                localStorage.setItem('token', sessionToken);
            } else if (localToken && !sessionToken) {
                sessionStorage.setItem('token', localToken);
            }
        } else {
            console.warn('[axios] 未找到认证令牌，请求可能会被拒绝');
        }

        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// 响应拦截器
axiosInstance.interceptors.response.use(
    response => {
        console.log(`[axios] 收到响应: ${response.status} 来自 ${response.config.url}`);
        return response;
    },
    error => {
        // 处理常见错误，如401未授权
        if (error.response) {
            console.error(`[axios] 请求错误: ${error.response.status} 来自 ${error.config?.url}`);

            const originalRequest = error.config;

            // 如果是401未授权错误，可能是token过期
            if (error.response.status === 401) {
                console.warn('[axios] 收到401未授权响应，可能需要重新登录');

                // 登录相关的API请求直接跳过，避免处理登录请求本身的401
                if (originalRequest.url?.includes('/users/login') ||
                    originalRequest.url?.includes('/users/token') ||
                    originalRequest._retry) {
                    localStorage.removeItem('token');
                    sessionStorage.removeItem('token');

                    // 如果不是登录页面，重定向到登录
                    if (window.location.pathname !== '/login') {
                        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                    }
                    return Promise.reject(error);
                }

                // 防止多个请求同时触发刷新
                if (!isRefreshing) {
                    isRefreshing = true;
                    console.log('[axios] 尝试重新获取Token或重定向到登录页...');

                    // 立即清除token并重定向到登录页
                    localStorage.removeItem('token');
                    sessionStorage.removeItem('token');

                    // 如果不是登录页面，重定向到登录页
                    if (window.location.pathname !== '/login') {
                        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
                    }

                    isRefreshing = false;
                    processQueue(error);
                    return Promise.reject(error);
                }
            }
        } else {
            console.error(`[axios] 请求错误: ${error.message}`);
        }

        return Promise.reject(error);
    }
);

export default axiosInstance; 