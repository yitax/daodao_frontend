<script setup>
import { ref, computed, onMounted, provide } from 'vue';
import { ElDatePicker } from 'element-plus';
import Summary from './Summary.vue';
import DailyTrend from './DailyTrend.vue';
import CategoryRanking from './CategoryRanking.vue';
import TransactionRanking from './TransactionRanking.vue';
import Ledger from './Ledger.vue';
import DailyReport from './DailyReport.vue';

// 标签页定义
const tabs = [
  { label: '收支总览', name: 'summary' },
  { label: '每日收支趋势', name: 'daily-trend' },
  { label: '分类排行', name: 'category-ranking' },
  { label: '明细排行', name: 'transaction-ranking' },
  { label: '明细账本', name: 'ledger' },
  { label: '每日报表', name: 'daily-report' },
];

// 当前激活的标签
const activeTab = ref('summary');

// 日期选择范围
const dateRange = ref([]);

// 验证并设置默认日期范围
const initializeDateRange = () => {
  // 检查现有日期范围是否有效
  if (!Array.isArray(dateRange.value) || dateRange.value.length !== 2 || 
      !dateRange.value[0] || !dateRange.value[1]) {
    console.log('[Reports] 日期范围无效或未设置，使用默认值（本月）');
    
    const today = new Date();
    
    // 设置为本月开始到今天
    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    dateRange.value = [
      firstDayOfMonth.toISOString().split('T')[0], // 本月第一天
      today.toISOString().split('T')[0] // 今天
    ];
  }
  
  console.log('[Reports] 初始化日期范围:', dateRange.value);
};

// 确保日期范围有效
const ensureValidDateRange = (range) => {
  // 如果没有传入有效的日期范围，使用当前值或默认值
  if (!Array.isArray(range) || range.length !== 2 || !range[0] || !range[1]) {
    console.warn('[Reports] 收到无效的日期范围，保持当前值');
    return dateRange.value;
  }
  
  try {
    // 确保日期格式正确
    const start = typeof range[0] === 'string' ? range[0] : range[0].toISOString().split('T')[0];
    const end = typeof range[1] === 'string' ? range[1] : range[1].toISOString().split('T')[0];
    return [start, end];
  } catch (error) {
    console.error('[Reports] 日期格式化错误:', error);
    return dateRange.value;
  }
};

// 处理日期变更
const handleDateChange = (value) => {
  console.log('[Reports] 日期范围变更:', value);
  
  if (Array.isArray(value) && value.length === 2) {
    dateRange.value = ensureValidDateRange(value);
  } else {
    console.warn('[Reports] 收到无效的日期范围值:', value);
    // 保持当前值
  }
};

// 初始化组件
onMounted(() => {
  console.log('[Reports] 组件已挂载');
  initializeDateRange();
});

// 提供安全的日期范围给子组件
const safeDateRange = computed(() => {
  return ensureValidDateRange(dateRange.value);
});

// 提供日期范围给需要的子组件
provide('dateRange', safeDateRange);

// 导航到指定标签
function navigateTo(tab) {
  activeTab.value = tab;
}
</script>

<template>
  <div class="reports-container">
    <div class="header">
      <h2 class="title">财务报表</h2>
      <div class="date-picker-container">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :clearable="false"
          :editable="false"
          @change="handleDateChange"
        />
      </div>
    </div>

    <div class="tabs">
      <div 
        v-for="tab in tabs" 
        :key="tab.name"
        :class="['tab-item', { active: activeTab === tab.name }]"
        @click="navigateTo(tab.name)"
      >
        {{ tab.label }}
      </div>
    </div>

    <div class="tab-content">
      <Summary v-if="activeTab === 'summary'" :date-range="safeDateRange" />
      <DailyTrend v-else-if="activeTab === 'daily-trend'" :date-range="safeDateRange" />
      <CategoryRanking v-else-if="activeTab === 'category-ranking'" :date-range="safeDateRange" />
      <TransactionRanking 
        v-else-if="activeTab === 'transaction-ranking'" 
        :date-range="dateRange" 
        @update:date-range="newRange => dateRange = newRange"
      />
      <Ledger v-else-if="activeTab === 'ledger'" :date-range="safeDateRange" />
      <DailyReport v-else-if="activeTab === 'daily-report'" :date-range="safeDateRange" />
    </div>
  </div>
</template>

<style scoped>
/* 保持原有样式 */
</style> 