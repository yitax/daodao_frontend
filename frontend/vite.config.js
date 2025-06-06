import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src')
        }
    },
    server: {
        port: 5173,
        open: true,
        proxy: {
            '/reports': {
                target: 'http://localhost:8000',
                changeOrigin: true
            },
            '/users': {
                target: 'http://localhost:8000',
                changeOrigin: true
            },
            '/transactions': {
                target: 'http://localhost:8000',
                changeOrigin: true
            },
            '/chat': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
}) 