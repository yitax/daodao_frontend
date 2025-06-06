<template>
  <el-config-provider>
    <div class="app-container">
      <div v-if="initializing" class="loading-container">
        <div class="loader"></div>
        <div class="loading-text">加载中，请稍候...</div>
      </div>
      <router-view v-else />
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from './store/user';
import { useRouter } from 'vue-router';

const initializing = ref(true);
const userStore = useUserStore();
const router = useRouter();

// 非阻塞方式检查认证状态
onMounted(async () => {
  console.log('[App] 组件挂载，初始化认证状态检查开始');
  
  try {
    // 只有在有token的情况下才尝试获取用户信息
    const hasToken = localStorage.getItem('token') || sessionStorage.getItem('token');
    
    if (hasToken) {
      console.log('[App] 发现token，尝试获取用户信息');
      await userStore.checkAuth();
      
      if (userStore.isLoggedIn) {
        console.log('[App] 认证成功，用户:', userStore.username);
      } else {
        console.log('[App] 认证失败，将在需要时重定向到登录页面');
        // 让router.beforeEach处理重定向
      }
    } else {
      console.log('[App] 未找到token，用户未登录状态');
    }
  } catch (error) {
    console.error('[App] 初始认证检查出错:', error);
  } finally {
    // 完成初始化
    initializing.value = false;
    console.log('[App] 初始化完成，解除加载状态');
  }
});
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #F0FBF7;
}

.loader {
  width: 60px;
  height: 60px;
  border: 5px solid #A7E0C7;
  border-radius: 50%;
  border-top-color: #5DAF8E;
  animation: spin 1s infinite ease-in-out;
  margin-bottom: 20px;
}

.loading-text {
  color: #3D6E59;
  font-size: 18px;
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style> 