<template>
  <div class="summary-container">
    <div v-if="authLoading" class="loading-overlay">
      <p style="text-align: center; margin-bottom: 20px;">正在检查登录状态，请稍候...</p>
      <el-skeleton :rows="3" animated />
    </div>
    <div v-else-if="loading && !error" class="loading-overlay">
      <el-skeleton :rows="6" animated />
    </div>
    <div v-else-if="error" class="error-message">
      <el-alert
        :title="errorMessage.includes('登录') ? '登录状态异常' : '加载失败'"
        :description="errorMessage"
        type="error"
        :closable="false"
        show-icon
      />
      <el-button v-if="!authLoading && errorMessage.includes('登录')" class="mt-4" type="primary" @click="goToLogin">去登录</el-button>
      <el-button v-if="!authLoading && !errorMessage.includes('登录')" class="mt-4" type="primary" @click="retryLoading">重试</el-button>
    </div>
    <template v-else-if="userStore.isLoggedIn && userStore.user">
      <div class="summary-cards">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card class="summary-card income-card">
              <div class="card-header">
                <span>总收入</span>
                <el-tooltip content="显示所选时间段内的总收入" placement="top">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="card-value">{{ totalIncome }}</div>
              <div class="card-footer">
                <span>{{ dateRangeText }}</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="summary-card expense-card">
              <div class="card-header">
                <span>总支出</span>
                <el-tooltip content="显示所选时间段内的总支出" placement="top">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="card-value">{{ totalExpense }}</div>
              <div class="card-footer">
                <span>{{ dateRangeText }}</span>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="summary-card balance-card">
              <div class="card-header">
                <span>结余</span>
                <el-tooltip content="总收入减去总支出" placement="top">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div class="card-value">{{ balance }}</div>
              <div class="card-footer">
                <span>{{ dateRangeText }}</span>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
      
      <el-divider />
      
      <div class="charts-container">
        <el-row :gutter="20">
          <!-- 交易频率统计 -->
          <el-col :span="12">
            <el-card class="chart-card">
              <div class="chart-header">
                <h3>交易频率统计</h3>
              </div>
              <div class="stats-container" v-if="!loading && !error">
                <div class="stat-item">
                  <div class="stat-label">
                    <span>交易总笔数</span>
                    <el-tooltip content="所选时间段内收支交易的总次数" placement="top">
                      <el-icon><InfoFilled /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="stat-value">{{ transactionStats.count || 0 }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">
                    <span>平均每笔收入</span>
                    <el-tooltip content="所选时间段内平均每笔收入的金额" placement="top">
                      <el-icon><InfoFilled /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="stat-value">{{ formatCurrency(transactionStats.avgIncome || 0) }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">
                    <span>平均每笔支出</span>
                    <el-tooltip content="所选时间段内平均每笔支出的金额" placement="top">
                      <el-icon><InfoFilled /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="stat-value">{{ formatCurrency(transactionStats.avgExpense || 0) }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">
                    <span>日均交易笔数</span>
                    <el-tooltip content="所选时间段内平均每天的交易笔数" placement="top">
                      <el-icon><InfoFilled /></el-icon>
                    </el-tooltip>
                  </div>
                  <div class="stat-value">{{ transactionStats.dailyAvg || 0 }}</div>
                </div>
              </div>
              <div v-else class="chart-placeholder">
                <el-skeleton :rows="4" animated />
              </div>
            </el-card>
          </el-col>
          
          <!-- 近期大额交易 -->
          <el-col :span="12">
            <el-card class="chart-card">
              <div class="chart-header">
                <h3>近期大额交易</h3>
                <el-tooltip content="显示所选时间段内金额最大的交易记录" placement="top">
                  <el-icon><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <div v-if="!loading && !error && largeTransactions.length > 0" class="large-transactions">
                <el-table :data="largeTransactions" style="width: 100%" size="small" stripe>
                  <el-table-column prop="date" label="日期" width="100">
                    <template #default="scope">
                      {{ formatDate(scope.row.date) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" min-width="120" show-overflow-tooltip />
                  <el-table-column prop="category" label="分类" width="100" show-overflow-tooltip />
                  <el-table-column prop="amount" label="金额" width="100" align="right">
                    <template #default="scope">
                      <span :class="scope.row.amount < 0 ? 'expense-text' : 'income-text'">
                        {{ formatCurrency(Math.abs(scope.row.amount)) }}
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-else-if="!loading && !error" class="chart-placeholder">
                <el-empty description="暂无大额交易记录" />
              </div>
              <div v-else class="chart-placeholder">
                <el-skeleton :rows="5" animated />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </template>
     <div v-else class="error-message">
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
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue';
import { InfoFilled } from '@element-plus/icons-vue';
import dayjs from 'dayjs';
import { 
  ElMessage, 
  ElSkeleton, 
  ElAlert, 
  ElButton, 
  ElCard, 
  ElRow, 
  ElCol, 
  ElIcon, 
  ElTooltip, 
  ElDivider, 
  ElEmpty,
  ElTable,
  ElTableColumn
} from 'element-plus';
import { useUserStore } from '../../store/user';
import { useRouter } from 'vue-router';
import axios from 'axios';

const userStore = useUserStore();
const router = useRouter();

// 创建一个API实例，专用于报表请求
const apiInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 添加请求拦截器，自动添加token和时间戳
apiInstance.interceptors.request.use(config => {
  console.log(`[Summary] 发送请求: ${config.method?.toUpperCase()} ${config.url}`);
  
  // 添加时间戳，防止缓存
  if (config.method?.toLowerCase() === 'get') {
    config.params = {
      ...config.params,
      _t: Date.now()
    };
  }
  
  // 添加认证token
  const sessionToken = sessionStorage.getItem('token');
  const localToken = localStorage.getItem('token');
  const token = sessionToken || localToken;
  
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
    // 确保两个存储都有token，防止刷新后丢失
    if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
      localStorage.setItem('token', sessionToken);
    } else if (localToken && !sessionToken) {
      sessionStorage.setItem('token', localToken);
    }
  }
  
  return config;
});

const props = defineProps({
  dateRange: {
    type: Array,
    default: () => [
      dayjs().subtract(29, 'day').format('YYYY-MM-DD'),
      dayjs().format('YYYY-MM-DD')
    ]
  }
});

const authLoading = ref(true);
const loading = ref(false);
const error = ref(false);
const errorMessage = ref('');

const dateRangeText = computed(() => {
  if (!props.dateRange || props.dateRange.length !== 2) return '';
  return `${props.dateRange[0]} 至 ${props.dateRange[1]}`;
});

const totalIncome = ref('¥ 0.00');
const totalExpense = ref('¥ 0.00');
const balance = ref('¥ 0.00');

// 收入支出图表数据
const categoryData = ref([]);

const goToLogin = () => {
  router.push({ name: 'login', query: { redirect: window.location.pathname + window.location.search } });
};

const retryLoading = () => {
  initializeAuthAndLoad();
};

// 加载收入支出总览数据
const loadIncomeExpenseData = async () => {
  console.log('[Summary] loadIncomeExpenseData - Start with dateRange:', props.dateRange);
  if (!props.dateRange || props.dateRange.length !== 2 || !props.dateRange[0] || !props.dateRange[1]) {
    console.warn('[Summary] loadIncomeExpenseData - Invalid date range');
    return;
  }

  loading.value = true;
  error.value = false;
  
  try {
    // 构造请求参数
    const params = {
      start_date: props.dateRange[0],
      end_date: props.dateRange[1]
    };
    
    console.log('[Summary] loadIncomeExpenseData - Fetching with params:', params);
    const response = await apiInstance.get('/reports/summary', { params });
    
    console.log('[Summary] loadIncomeExpenseData - API response received:', response);
    if (response && response.data) {
      console.log('[Summary] loadIncomeExpenseData - Data from API:', response.data);
      
      // 格式化金额为货币形式
      const formatCurrency = (amount) => {
        return `¥ ${Number(amount).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
      };
      
      totalIncome.value = formatCurrency(response.data.total_income || 0);
      totalExpense.value = formatCurrency(response.data.total_expense || 0);
      balance.value = formatCurrency(response.data.balance || 0);
      
      console.log('[Summary] loadIncomeExpenseData - Data processed:', { 
        totalIncome: totalIncome.value,
        totalExpense: totalExpense.value,
        balance: balance.value
      });
    } else {
      console.warn('[Summary] loadIncomeExpenseData - API response or response.data is undefined.');
      throw new Error('从服务器获取数据格式不正确');
    }
  } catch (err) {
    console.error('[Summary] loadIncomeExpenseData - Error:', err);
    error.value = true;
    errorMessage.value = err.response && err.response.data?.detail 
      ? `加载失败: ${err.response.data.detail}` 
      : '加载收入支出数据失败，请稍后再试';
    
    // 重置为0
    totalIncome.value = '¥ 0.00';
    totalExpense.value = '¥ 0.00';
    balance.value = '¥ 0.00';
  } finally {
    loading.value = false;
  }
};

// 加载概览数据（将来可能用于图表等）
const loadOverviewData = async () => {
  console.log('[Summary] loadOverviewData - Start');
  // 功能开发中，目前只记录日志
  // 将来这里可以添加额外的概览数据加载逻辑
};

// 加载分类数据（将来可能用于饼图）
const loadCategoryData = async () => {
  console.log('[Summary] loadCategoryData - Start');
  // 功能开发中，目前只记录日志
  // 将来这里可以添加分类数据加载逻辑
};

// 格式化货币
const formatCurrency = (amount) => {
  return `¥ ${Number(amount).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return dayjs(dateStr).format('MM-DD');
};

// 交易统计数据
const transactionStats = ref({
  count: 0,         // 交易总笔数
  avgIncome: 0,     // 平均每笔收入
  avgExpense: 0,    // 平均每笔支出
  dailyAvg: 0       // 日均交易笔数
});

// 大额交易记录
const largeTransactions = ref([]);

// 加载交易统计数据
const loadTransactionStats = async () => {
  console.log('[Summary] loadTransactionStats - Start with dateRange:', props.dateRange);
  if (!props.dateRange || props.dateRange.length !== 2 || !props.dateRange[0] || !props.dateRange[1]) {
    console.warn('[Summary] loadTransactionStats - Invalid date range');
    return;
  }

  try {
    // 构造请求参数
    const params = {
      start_date: props.dateRange[0],
      end_date: props.dateRange[1],
      include_stats: true
    };
    
    console.log('[Summary] loadTransactionStats - Fetching with params:', params);
    const response = await apiInstance.get('/reports/summary', { params });
    
    if (response && response.data && response.data.transaction_stats) {
      console.log('[Summary] loadTransactionStats - Data from API:', response.data.transaction_stats);
      
      transactionStats.value = {
        count: response.data.transaction_stats.total_count || 0,
        avgIncome: response.data.transaction_stats.avg_income || 0,
        avgExpense: response.data.transaction_stats.avg_expense || 0,
        dailyAvg: response.data.transaction_stats.daily_avg || 0
      };
    } else {
      console.warn('[Summary] loadTransactionStats - Transaction stats not found in API response');
      // 重置为默认值
      transactionStats.value = {
        count: 0,
        avgIncome: 0,
        avgExpense: 0,
        dailyAvg: 0
      };
    }
  } catch (err) {
    console.error('[Summary] loadTransactionStats - Error:', err);
    // 出错时重置为默认值
    transactionStats.value = {
      count: 0,
      avgIncome: 0,
      avgExpense: 0,
      dailyAvg: 0
    };
  }
};

// 加载大额交易数据
const loadLargeTransactions = async () => {
  console.log('[Summary] loadLargeTransactions - Start with dateRange:', props.dateRange);
  if (!props.dateRange || props.dateRange.length !== 2 || !props.dateRange[0] || !props.dateRange[1]) {
    console.warn('[Summary] loadLargeTransactions - Invalid date range');
    return;
  }

  try {
    // 构造请求参数 - 获取支出和收入的大额交易
    const params = {
      start_date: props.dateRange[0],
      end_date: props.dateRange[1],
      limit: 5,  // 最多显示5条记录
      sort_by: 'amount',
      sort_order: 'abs_desc'  // 按金额绝对值降序排序
    };
    
    console.log('[Summary] loadLargeTransactions - Fetching with params:', params);
    const response = await apiInstance.get('/reports/large-transactions', { params });
    
    if (response && response.data && response.data.transactions) {
      console.log('[Summary] loadLargeTransactions - Data from API:', response.data.transactions);
      largeTransactions.value = response.data.transactions;
    } else {
      console.warn('[Summary] loadLargeTransactions - Large transactions not found in API response');
      largeTransactions.value = [];
    }
  } catch (err) {
    console.error('[Summary] loadLargeTransactions - Error:', err);
    largeTransactions.value = [];
  }
};

// 更新初始化和加载函数，添加新的数据加载
const initializeAuthAndLoad = async () => {
  console.log('[Summary] initializeAuthAndLoad - Start');
  authLoading.value = true;
  error.value = false;
  
  try {
    if (!userStore.isLoggedIn) {
      console.log('[Summary] initializeAuthAndLoad - Not logged in, checking auth');
      await userStore.checkAuth();
    }
    
    authLoading.value = false;
    
    // 如果已登录，加载数据
    if (userStore.isLoggedIn && userStore.user) {
      console.log('[Summary] initializeAuthAndLoad - User is logged in, loading data');
      await Promise.all([
        loadIncomeExpenseData(),
        loadTransactionStats(),
        loadLargeTransactions()
      ]);
    } else {
      console.warn('[Summary] initializeAuthAndLoad - User not logged in after auth check');
      error.value = true;
      errorMessage.value = '登录状态已过期，请重新登录';
    }
  } catch (err) {
    console.error('[Summary] initializeAuthAndLoad - Error:', err);
    authLoading.value = false;
    error.value = true;
    errorMessage.value = err.message || '初始化失败，请重试';
  }
};

// 监听日期范围变化，重新加载数据
watch(() => props.dateRange, async (newDateRange, oldDateRange) => {
  console.log('[Summary] Date range changed:', newDateRange);
  
  // 只有当日期范围真正改变且有效时才重新加载
  if (
    newDateRange && 
    newDateRange.length === 2 && 
    newDateRange[0] && 
    newDateRange[1] && 
    (
      !oldDateRange || 
      oldDateRange.length !== 2 || 
      newDateRange[0] !== oldDateRange[0] || 
      newDateRange[1] !== oldDateRange[1]
    )
  ) {
    console.log('[Summary] Valid date range change, reloading data');
    await Promise.all([
      loadIncomeExpenseData(),
      loadTransactionStats(),
      loadLargeTransactions()
    ]);
  } else {
    console.log('[Summary] Date range invalid or unchanged, not reloading');
  }
}, { immediate: false });

// 组件挂载时初始化
onMounted(() => {
  console.log('[Summary] Component mounted');
  initializeAuthAndLoad();
});

</script>

<style scoped>
.summary-container {
  padding: 20px;
  height: 100%;
}

.loading-overlay {
  padding: 20px;
}

.error-message {
  padding: 20px;
  text-align: center;
}

.mt-4 {
  margin-top: 16px;
}

.summary-cards {
  margin-bottom: 20px;
}

.summary-card {
  height: 100%;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.income-card {
  background: linear-gradient(135deg, #e3f9ee, #d1f0e6);
  border: 1px solid #a0e1c7;
}

.expense-card {
  background: linear-gradient(135deg, #fff1f0, #ffe9e8);
  border: 1px solid #ffc6c4;
}

.balance-card {
  background: linear-gradient(135deg, #e8f4ff, #dcedff);
  border: 1px solid #b8d9ff;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 15px;
  color: #333;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}

.card-footer {
  font-size: 13px;
  color: #666;
}

.chart-card {
  margin-bottom: 20px;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 100%;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #3D6E59;
}

.chart-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.chart-content {
  height: 280px;
}

/* 新增样式 */
.stats-container {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  padding: 0 10px;
}

.stat-item {
  background-color: #f0f8f5;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.stat-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: #555;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #3D6E59;
}

.large-transactions {
  max-height: 300px;
  overflow-y: auto;
}

.expense-text {
  color: #e74c3c;
}

.income-text {
  color: #3D6E59;
}

:deep(.el-table .el-table__row) {
  cursor: default;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f0f8f5;
}

:deep(.el-table__header-wrapper th) {
  background-color: #e3f2ed;
  color: #3D6E59;
  font-weight: 600;
}

.charts-container {
  margin-top: 20px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .stats-container {
    grid-template-columns: 1fr;
  }
}
</style> 