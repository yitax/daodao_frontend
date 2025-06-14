import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// 获取API URL，在配置文件中应该使用process.env
// 对于本地开发使用8000端口，容器内使用空字符串(通过相对路径请求)
const apiBase = process.env.VITE_API_BASE_URL || 'http://localhost:8000'
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src')
        }
    },
    base: '/',
    server: {
        port: 5173,
        open: true,
        proxy: {
            '/users': {
                target: apiBase,
                changeOrigin: true,
            },
            '/transactions': {
                target: apiBase,
                changeOrigin: true,
            },
            '/reports': {
                target: apiBase,
                changeOrigin: true,
            },
            '/chat': {
                target: apiBase,
                changeOrigin: true,
            }
        },
        historyApiFallback: true
    },
    build: {
        outDir: 'dist',
        assetsDir: 'assets',
        // 确保生产构建过程中也能正确使用环境变量
        define: {
            'process.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || '')
        }
    }
}) 