<template>
  <div class="app-container">
    <el-config-provider :locale="zhCn">
      <router-view v-if="isReady" />
      <div v-else class="loading-container">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
    </el-config-provider>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { ElConfigProvider } from "element-plus";
import { Loading } from "@element-plus/icons-vue";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";
import { useUserStore } from "./store/user";

const isReady = ref(false);
const userStore = useUserStore();

onMounted(async () => {
  console.log('[App] 应用启动，检查认证状态...');
  try {
    // Check if token exists in any storage
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!localToken || !!sessionToken;
    
    if (hasToken) {
      console.log('[App] 找到token，尝试恢复会话...');
      // Ensure token is synchronized between storages
      if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
        console.log('[App] 将sessionStorage中的token同步到localStorage');
        localStorage.setItem('token', sessionToken);
      } else if (localToken && !sessionToken) {
        console.log('[App] 将localStorage中的token同步到sessionStorage');
        sessionStorage.setItem('token', localToken);
      }
      
      await userStore.checkAuth();
      console.log('[App] 认证状态检查完成，用户状态:', userStore.isLoggedIn ? '已登录' : '未登录');
    } else {
      console.log('[App] 未找到token，用户未登录');
    }
  } catch (error) {
    console.error('[App] 检查认证状态时出错:', error);
  } finally {
    // 无论成功失败都标记为已准备好，因为路由会处理未登录状态
    isReady.value = true;
  }
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
  width: 100%;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}

.app-container {
  height: 100vh;
  width: 100vw;
}

.loading-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.loading-icon {
  font-size: 48px;
  color: #409eff;
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style> 