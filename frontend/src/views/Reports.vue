<template>
  <div class="reports-page">
    <div class="reports-container">
      <div class="page-header">
        <h2>财务报表</h2>
        <div class="date-filter">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
          />
        </div>
      </div>
      
      <el-tabs v-model="activeTab" @tab-click="handleTabChange" class="report-tabs">
        <el-tab-pane label="收支总览" name="summary"></el-tab-pane>
        <el-tab-pane label="每日收支趋势" name="daily"></el-tab-pane>
        <el-tab-pane label="分类排行" name="category"></el-tab-pane>
        <el-tab-pane label="明细排行" name="ranking"></el-tab-pane>
        <el-tab-pane label="每日报表" name="ledger"></el-tab-pane>
      </el-tabs>
      
      <div class="report-view-container">
        <router-view v-if="isAuthenticated" :key="`${activeTab}-${dateRangeKey}-${routeKey}`" :date-range="dateRange" />
        <div v-else class="auth-error">
          <el-alert
            title="访问受限"
            description="请您先登录才能查看财务报表。"
            type="warning"
            :closable="false"
            show-icon
          />
          <el-button class="mt-4" type="primary" @click="goToLogin">去登录</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import dayjs from 'dayjs';
import { useUserStore } from '../store/user';
import { ElMessage, ElAlert, ElButton } from 'element-plus';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 默认显示最近30天
const defaultDateRange = [
  dayjs().subtract(29, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD')
];

const dateRange = ref(defaultDateRange);
const dateRangeKey = ref(0); // 用于强制更新组件
const routeKey = ref(0); // 用于路由变化时强制更新组件
const isAuthenticated = ref(true); // 默认假设已认证，后续检查

// 根据当前路由路径确定活动标签
const getActiveTab = (path) => {
  if (path.includes('/reports/summary')) return 'summary';
  if (path.includes('/reports/daily')) return 'daily';
  if (path.includes('/reports/category')) return 'category';
  if (path.includes('/reports/ranking')) return 'ranking';
  if (path.includes('/reports/ledger')) return 'ledger';
  return 'summary'; // 默认
};

const activeTab = ref(getActiveTab(route.path));

// 监听路由变化更新活动标签和强制刷新组件
watch(
  () => route.path,
  (path) => {
    console.log('[Reports] Route changed:', path);
    activeTab.value = getActiveTab(path);
    routeKey.value += 1; // 路由变化时增加key，强制刷新组件
  }
);

// 处理标签切换
const handleTabChange = (tab) => {
  const tabName = tab.props.name;
  console.log('[Reports] Tab clicked:', tabName, 'Current active tab:', activeTab.value);
  
  if (tabName === activeTab.value) {
    // 如果点击当前激活的标签，刷新组件
    console.log('[Reports] Refreshing current tab');
    refreshComponent();
    return;
  }
  
  // 检查认证状态
  checkAuthBeforeNavigation(() => {
    console.log('[Reports] Navigating to tab:', tabName);
    router.push(`/reports/${tabName}`);
  });
};

// 刷新组件
const refreshComponent = () => {
  console.log('[Reports] Refreshing component, increasing dateRangeKey');
  dateRangeKey.value += 1;
};

// 处理日期范围变化
const handleDateRangeChange = (val) => {
  console.log('[Reports] Date range changed:', val);
  dateRange.value = val || defaultDateRange;
  refreshComponent(); // 日期变化时刷新组件
};

// 去登录页
const goToLogin = () => {
  router.push({ name: 'login', query: { redirect: route.fullPath } });
};

// 检查认证状态
const checkAuthBeforeNavigation = (callback) => {
  console.log('[Reports] Checking auth before navigation');
  
  // 检查是否有token
  const sessionToken = sessionStorage.getItem('token');
  const localToken = localStorage.getItem('token');
  const hasToken = !!localToken || !!sessionToken;
  
  if (!hasToken) {
    console.warn('[Reports] No token found');
    isAuthenticated.value = false;
    ElMessage.warning('您需要先登录才能查看报表');
    return;
  }
  
  // 确保token在两个存储位置都同步
  if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
    console.log('[Reports] Syncing token from sessionStorage to localStorage');
    localStorage.setItem('token', sessionToken);
  } else if (localToken && !sessionToken) {
    console.log('[Reports] Syncing token from localStorage to sessionStorage');
    sessionStorage.setItem('token', localToken);
  }
  
  // 如果已登录但用户信息不存在，尝试恢复会话
  if (!userStore.isLoggedIn) {
    console.log('[Reports] Token exists but not logged in, checking auth');
    userStore.checkAuth().then(() => {
      if (userStore.isLoggedIn) {
        console.log('[Reports] Auth check successful');
        isAuthenticated.value = true;
        callback();
      } else {
        console.warn('[Reports] Auth check failed');
        isAuthenticated.value = false;
        ElMessage.warning('登录已过期，请重新登录');
      }
    }).catch((err) => {
      console.error('[Reports] Auth check error:', err);
      isAuthenticated.value = false;
      ElMessage.error('验证登录状态失败，请重新登录');
    });
  } else {
    console.log('[Reports] Already logged in');
    isAuthenticated.value = true;
    callback();
  }
};

onMounted(() => {
  // 初始化时检查认证状态
  console.log('[Reports] Component mounted');
  checkAuthBeforeNavigation(() => {
    console.log('[Reports] Auth check on mount successful');
  });
});
</script>

<style scoped>
.reports-page {
  height: 100%;
  background-color: #E3F2ED;
}

.reports-container {
  background-color: #F0FBF7;
  border-radius: 20px;
  box-shadow: 0 8px 20px rgba(61, 110, 89, 0.15);
  border: 3px solid #A7E0C7;
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px dashed #8CDAB6;
}

.page-header h2 {
  margin: 0;
  color: #3D6E59;
  font-weight: 600;
  font-size: 24px;
  letter-spacing: 1px;
}

.report-tabs {
  margin-bottom: 20px;
}

/* 薄荷绿风格的标签页 */
:deep(.el-tabs__item) {
  font-size: 15px;
  color: #5DAF8E;
  padding: 0 16px;
  transition: all 0.3s;
}

:deep(.el-tabs__item:hover) {
  color: #3D6E59;
}

:deep(.el-tabs__item.is-active) {
  color: #2A4D3E;
  font-weight: bold;
}

:deep(.el-tabs__active-bar) {
  background-color: #5DAF8E;
  height: 3px;
  border-radius: 3px;
}

:deep(.el-tabs__nav-wrap::after) {
  background-color: #C6F7E2;
  height: 2px;
}

.date-filter {
  display: flex;
  align-items: center;
}

/* 薄荷绿风格的日期选择器 */
.date-filter :deep(.el-date-editor) {
  --el-date-editor-width: auto;
  border-radius: 18px;
  border: 2px solid #8CDAB6;
  padding: 0 10px;
  background-color: white;
}

.date-filter :deep(.el-input__wrapper) {
  background: none;
  box-shadow: none;
}

.date-filter :deep(.el-input__inner) {
  color: #3D6E59;
}

.date-filter :deep(.el-range-separator) {
  color: #5DAF8E;
}

.report-view-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.auth-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  flex-grow: 1;
  background-color: #fff;
  border-radius: 20px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px dashed #8CDAB6;
}

.auth-error :deep(.el-alert) {
  border-radius: 15px;
  border: 1px solid #C6F7E2;
}

.auth-error :deep(.el-button) {
  border-radius: 20px;
  background-color: #5DAF8E;
  border-color: #5DAF8E;
  font-size: 15px;
  padding: 10px 24px;
}

.auth-error :deep(.el-button:hover) {
  background-color: #3D6E59;
  border-color: #3D6E59;
}

.mt-4 {
  margin-top: 16px;
}
</style> 