import { createApp } from 'vue'
import './assets/main.css'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { useUserStore } from './store/user'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 初始化前检查登录状态
(function checkLoginBeforeInit() {
    const path = window.location.pathname;
    // 确保当前路由不是登录相关页面
    const isAuthPage = path === '/login' || path.includes('/login') ||
        path === '/register' || path.includes('/register');

    if (!isAuthPage) {
        const hasToken = !!localStorage.getItem('token') || !!sessionStorage.getItem('token');
        if (!hasToken) {
            console.log('未检测到登录令牌，重定向到登录页面');
            // 确保使用正确的路径，不含域名部分，这样在任何环境都能工作
            const loginPath = '/login';
            const redirectParam = path && path !== '/' ? `?redirect=${encodeURIComponent(path)}` : '';

            // 使用window.location.href进行导航而不是Vue Router(因为Router此时还没初始化)
            // 注意：不使用replace以确保用户可以返回
            window.location.href = loginPath + redirectParam;
        }
    }
})();

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
    locale: zhCn,
    size: 'default',
    zIndex: 3000
})

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

// 检查初始认证状态
const userStore = useUserStore(pinia)

// 异步初始化应用
async function initApp() {
    console.log("应用初始化: 检查认证状态...")
    try {
        // 尝试从token恢复会话
        await userStore.checkAuth()
    } catch (error) {
        console.error("初始化认证检查失败:", error)
        // 即使认证检查失败，也继续启动应用
    } finally {
        // 无论认证状态如何，都挂载应用
        console.log("应用初始化完成，当前认证状态:", userStore.isLoggedIn ? "已登录" : "未登录")
        app.mount('#app')
    }
}

initApp() 