<template>
  <div class="settings-page">
    <div class="settings-container">
      <div class="page-header">
        <h2>设置</h2>
      </div>
      
      <el-tabs v-model="activeTab" @tab-change="handleTabChange" class="settings-tabs">
        <el-tab-pane label="AI个性设置" name="personality"></el-tab-pane>
        <el-tab-pane label="账户设置" name="account"></el-tab-pane>
      </el-tabs>
      
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

// 根据当前路由路径确定活动标签
const getActiveTab = (path) => {
  if (path.includes('/settings/personality')) return 'personality';
  if (path.includes('/settings/account')) return 'account';
  return 'personality'; // 默认
};

const activeTab = ref(getActiveTab(route.path));

// 监听路由变化更新活动标签
watch(
  () => route.path,
  (path) => {
    activeTab.value = getActiveTab(path);
  }
);

// 处理标签切换
const handleTabChange = (tabName) => {
  router.push(`/settings/${tabName}`);
};
</script>

<style scoped>
.settings-page {
  height: 100%;
}

.settings-container {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
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
}

.page-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-weight: 500;
}

.settings-tabs {
  margin-bottom: 20px;
}
</style> 