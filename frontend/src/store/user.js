import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// 创建HTTP客户端
const api = axios.create({
    baseURL: '',  // 修改为空字符串，使用相对路径直接访问
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
})

// 添加拦截器以记录API请求
api.interceptors.request.use(config => {
    console.log(`发送请求: ${config.method.toUpperCase()} ${config.url}`)
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

    // 新增：AI助手相关状态
    const personalities = ref([])
    const currentPersonalityId = ref(null)

    const isLoggedIn = computed(() => !!token.value)
    const username = computed(() => user.value?.username || '未登录')

    // 新增：根据ID查找助手信息
    const currentPersonality = computed(() => {
        return personalities.value.find(p => p.id === currentPersonalityId.value) || personalities.value[0] || null
    })

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
            await fetchPersonalities()
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
            console.log('准备注册用户:', { username, email, password: '***' });

            // 打印完整请求信息
            console.log('注册请求URL:', '/users/register');
            console.log('注册请求数据:', JSON.stringify({
                username,
                email,
                password
            }));

            const response = await api.post('/users/register', {
                username,
                email,
                password
            });

            console.log('注册成功，响应数据:', response.data);
            await login(username, password, true);
            return true;
        } catch (err) {
            console.error('---------- 注册失败 ----------');
            console.error('错误对象:', err);

            if (err.response) {
                console.error('状态码:', err.response.status);
                console.error('响应头:', err.response.headers);
                console.error('响应数据:', err.response.data);
                console.error('原始响应:', err.response);

                // 尝试多种方式提取错误信息
                let errorMessage = '';

                if (typeof err.response.data === 'object') {
                    console.log('数据类型: 对象');
                    if (err.response.data.detail) {
                        errorMessage = err.response.data.detail;
                        console.log('从detail字段提取错误信息:', errorMessage);
                    } else {
                        console.log('对象中没有detail字段');
                        errorMessage = JSON.stringify(err.response.data);
                    }
                } else if (typeof err.response.data === 'string') {
                    console.log('数据类型: 字符串');
                    errorMessage = err.response.data;
                    console.log('使用整个字符串作为错误信息:', errorMessage);
                } else {
                    console.log('未知数据类型:', typeof err.response.data);
                    errorMessage = `错误 (${err.response.status})`;
                }

                // 保存错误信息
                error.value = errorMessage || '注册失败，请稍后再试';
                console.log('最终错误信息:', error.value);
            } else if (err.request) {
                console.error('请求已发送但没有收到响应');
                error.value = '服务器无响应，请检查网络连接';
            } else {
                console.error('请求配置错误:', err.message);
                error.value = `请求错误: ${err.message}`;
            }

            console.error('---------- 错误处理结束 ----------');
            return false;
        } finally {
            loading.value = false;
        }
    }

    async function fetchUserInfo() {
        if (!token.value) return null

        loading.value = true
        try {
            const response = await api.get('/users/me')
            user.value = response.data
            await fetchUserSettings()
            return user.value
        } catch (error) {
            console.error('获取用户信息失败:', error)
            logout()
            throw error
        } finally {
            loading.value = false
        }
    }

    // 新增：获取用户设置（包括助手ID，优先从localStorage读取）
    async function fetchUserSettings() {
        try {
            // 优先从localStorage读取
            const localPersonalityId = localStorage.getItem('personality_id')

            if (localPersonalityId) {
                console.log(`[UserStore] 从本地存储读取personality_id: ${localPersonalityId}`)
                currentPersonalityId.value = parseInt(localPersonalityId, 10)
                return
            }

            // 如果本地没有，尝试从服务器获取
            try {
                const response = await api.get('/users/settings')
                currentPersonalityId.value = response.data.personality_id
                // 保存到localStorage以备将来使用
                localStorage.setItem('personality_id', response.data.personality_id)
            } catch (serverError) {
                console.error('从服务器获取用户设置失败:', serverError)
                // 如果服务器获取也失败，设置默认值
                currentPersonalityId.value = 1
                localStorage.setItem('personality_id', '1')
            }
        } catch (error) {
            console.error('获取用户设置失败:', error)
            // 如果整个过程失败，设置默认值
            currentPersonalityId.value = 1
            localStorage.setItem('personality_id', '1')
        }
    }

    // 新增：获取所有AI助手列表
    async function fetchPersonalities() {
        try {
            const response = await api.get('/chat/personalities');
            if (response.data && response.data.length > 0) {
                personalities.value = response.data;
            }
        } catch (error) {
            console.error('获取AI助手列表失败:', error);
            personalities.value = []; // 出错时清空
        }
    }

    // 新增：更新用户设置（使用localStorage存储）
    async function updateUserSettings(settings) {
        try {
            // 保存到本地存储而不是发送到服务器
            if (settings.personality_id) {
                // 更新状态
                currentPersonalityId.value = settings.personality_id
                // 保存到localStorage
                localStorage.setItem('personality_id', settings.personality_id)
                console.log(`[UserStore] 保存personality_id到本地存储: ${settings.personality_id}`)
            }
            return { success: true }
        } catch (error) {
            console.error('更新用户设置失败:', error)
            throw new Error('更新设置失败，请稍后再试')
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
                // 成功获取用户信息后，也获取助手列表
                await fetchPersonalities()
                console.log('[UserStore] 用户信息和助手列表获取成功:', userData?.username)
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
        // 登出时不清除personality_id，保留用户的偏好设置
        // localStorage.removeItem('personality_id')

        // 新增：登出时清空助手列表，但保留选择的ID
        personalities.value = []
        // 保留currentPersonalityId.value，不设为null
    }

    return {
        user,
        token,
        loading,
        error,
        isLoggedIn,
        username,
        personalities,
        currentPersonalityId,
        currentPersonality,
        login,
        register,
        fetchUserInfo,
        checkAuth,
        logout,
        api,
        fetchPersonalities,
        updateUserSettings
    }
}) 