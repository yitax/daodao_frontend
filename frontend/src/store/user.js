import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// 创建HTTP客户端
const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
})

// 添加拦截器以记录API请求
api.interceptors.request.use(config => {
    console.log(`发送请求: ${config.method.toUpperCase()} ${config.baseURL}${config.url}`)
    return config
})

// 添加响应拦截器以记录响应
api.interceptors.response.use(
    response => {
        console.log(`收到响应: ${response.status} 来自 ${response.config.url}`)
        return response
    },
    error => {
        if (error.response) {
            console.error(`请求错误: ${error.response.status} 来自 ${error.config.url}`)

            // 如果是401错误，清除token并重定向到登录页
            if (error.response.status === 401) {
                console.warn('收到401未授权响应，可能需要重新登录')
                // 不在这里调用logout()，避免循环依赖，让调用方处理
            }
        } else {
            console.error(`请求错误: ${error.message}`)
        }
        return Promise.reject(error)
    }
)

// 添加请求拦截器，自动添加token
api.interceptors.request.use(config => {
    // 优先使用会话存储的token，其次使用本地存储的token
    const sessionToken = sessionStorage.getItem('token')
    const localToken = localStorage.getItem('token')
    const token = sessionToken || localToken

    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
        // 确保两个存储都有token，防止刷新后丢失
        if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
            localStorage.setItem('token', sessionToken)
        } else if (localToken && !sessionToken) {
            sessionStorage.setItem('token', localToken)
        }
    }
    return config
})

export const useUserStore = defineStore('user', () => {
    const user = ref(null)
    const token = ref(sessionStorage.getItem('token') || localStorage.getItem('token') || '')
    const loading = ref(false)
    const error = ref(null)

    const isLoggedIn = computed(() => !!token.value)
    const username = computed(() => user.value?.username || '未登录')

    async function login(username, password, rememberMe = false) {
        loading.value = true
        error.value = null
        try {
            const formData = new FormData()
            formData.append('username', username)
            formData.append('password', password)

            const response = await api.post('/users/login', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })

            const { access_token } = response.data
            token.value = access_token

            // 如果选择记住我，则存储在localStorage，否则存储在sessionStorage
            if (rememberMe) {
                localStorage.setItem('token', access_token)
                localStorage.setItem('rememberMe', 'true')
                // Also store in sessionStorage for immediate use
                sessionStorage.setItem('token', access_token)
            } else {
                sessionStorage.setItem('token', access_token)
                localStorage.removeItem('rememberMe')
                localStorage.removeItem('token')
            }

            await fetchUserInfo()
            return true
        } catch (error) {
            console.error('登录失败:', error)
            error.value = error.response?.data?.detail || '登录失败，请检查用户名和密码'
            user.value = null
            token.value = ''
            localStorage.removeItem('token')
            localStorage.removeItem('rememberMe')
            sessionStorage.removeItem('token')
            return false
        } finally {
            loading.value = false
        }
    }

    async function register(username, email, password) {
        loading.value = true
        error.value = null
        try {
            const response = await api.post('/users/register', {
                username,
                email,
                password
            })
            await login(username, password, true)
            return true
        } catch (error) {
            console.error('注册失败:', error)
            error.value = error.response?.data?.detail || '注册失败，请稍后再试'
            return false
        } finally {
            loading.value = false
        }
    }

    async function fetchUserInfo() {
        if (!token.value) return null

        loading.value = true
        try {
            const response = await api.get('/users/me')
            user.value = response.data
            return user.value
        } catch (error) {
            console.error('获取用户信息失败:', error)
            logout()
            throw error
        } finally {
            loading.value = false
        }
    }

    async function checkAuth() {
        // 检查localStorage和sessionStorage中是否有token
        const localToken = localStorage.getItem('token')
        const sessionToken = sessionStorage.getItem('token')

        console.log('[UserStore] 检查认证状态:', {
            localToken: localToken ? '存在' : '不存在',
            sessionToken: sessionToken ? '存在' : '不存在',
            currentToken: token.value ? '已设置' : '未设置',
            currentUser: user.value ? '已加载' : '未加载'
        })

        if (localToken || sessionToken) {
            // 更新当前token
            token.value = localToken || sessionToken

            // 确保两个存储位置都有token，以防止刷新问题
            if (localToken && !sessionToken) {
                sessionStorage.setItem('token', localToken);
            }

            console.log('[UserStore] 发现token，尝试获取用户信息...')

            try {
                const userData = await fetchUserInfo()
                console.log('[UserStore] 用户信息获取成功:', userData?.username)
                return userData
            } catch (error) {
                console.error('[UserStore] 获取用户信息失败，清除token:', error)
                logout()
                return null
            }
        } else {
            console.log('[UserStore] 未找到token')
            // 确保状态一致
            if (token.value) {
                console.warn('[UserStore] 存储中无token但状态中有token，清除状态')
                logout()
            }
            return null
        }
    }

    function logout() {
        console.log('[UserStore] 执行登出操作，清除用户状态和token')
        user.value = null
        token.value = ''
        localStorage.removeItem('token')
        localStorage.removeItem('rememberMe')
        sessionStorage.removeItem('token')
    }

    return {
        user,
        token,
        loading,
        error,
        isLoggedIn,
        username,
        login,
        register,
        fetchUserInfo,
        checkAuth,
        logout,
        api
    }
}) 