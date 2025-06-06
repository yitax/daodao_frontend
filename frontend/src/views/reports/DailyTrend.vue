<template>
  <div class="daily-trend">
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
    <template v-else>
    <div class="chart-container">
      <div class="chart-header">
        <h3>每日收支趋势</h3>
      </div>
      <div class="chart-content">
          <div v-if="chartLoading" class="chart-placeholder">
          <el-empty description="正在加载图表..." />
          </div>
          <div v-else-if="chartData.length === 0" class="chart-placeholder">
            <el-empty description="没有找到数据" />
          </div>
          <div v-else id="dailyTrendChart" class="chart"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import { ElMessage, ElSkeleton, ElAlert, ElButton } from 'element-plus';
import * as echarts from 'echarts';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../store/user';

const router = useRouter();
const userStore = useUserStore();

// 创建axios实例
const apiInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 添加请求拦截器，自动添加token
apiInstance.interceptors.request.use(config => {
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
    required: true
  }
});

const chartData = ref([]);
const loading = ref(false);
const chartLoading = ref(false);
const error = ref(false);
const errorMessage = ref('');
const authLoading = ref(true);
let chart = null;

// 去登录页
const goToLogin = () => {
  router.push({ name: 'login', query: { redirect: window.location.pathname + window.location.search } });
};

// 重试加载数据
const retryLoading = () => {
  initializeAuthAndLoad();
};

// 监听日期范围变化，加载数据
watch(
  () => props.dateRange,
  (newRange, oldRange) => {
    console.log('[DailyTrend] dateRange changed:', { newRange, oldRange });
    
    // 防止初始化时重复加载
    if (authLoading.value) {
      console.log('[DailyTrend] Skipping watcher during auth loading');
      return;
    }
    
    if (newRange && newRange.length === 2 && JSON.stringify(newRange) !== JSON.stringify(oldRange)) {
      console.log('[DailyTrend] Loading data due to dateRange change');
      loadChartData(newRange);
    }
  }
);

// 加载图表数据
const loadChartData = async (dateRange) => {
  console.log('[DailyTrend] loadChartData - Start. Date range:', dateRange);
  chartLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  
  try {
    // 检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[DailyTrend] loadChartData: No token found. Aborting.');
      error.value = true;
      errorMessage.value = '您未登录或登录已过期，请重新登录。';
      return;
    }
    
    // 确保token在两个存储位置都存在
    if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
      localStorage.setItem('token', sessionToken);
    } else if (localToken && !sessionToken) {
      sessionStorage.setItem('token', localToken);
    }
    
    if (!userStore.isLoggedIn) {
      console.log('[DailyTrend] loadChartData: Token exists but user not logged in. Attempting to restore session...');
      try {
        await userStore.checkAuth();
        if (!userStore.isLoggedIn) {
          console.warn('[DailyTrend] loadChartData: Failed to restore session.');
          error.value = true;
          errorMessage.value = '您的登录已失效，请重新登录。';
          return;
        }
      } catch (err) {
        console.error('[DailyTrend] loadChartData: Error restoring session:', err);
        error.value = true;
        errorMessage.value = '恢复会话失败，请重新登录。';
        return;
      }
    }
    
    console.log('[DailyTrend] loadChartData - Making API request');
    const response = await apiInstance.get('/reports/daily', {
      params: {
        start_date: dateRange[0],
        end_date: dateRange[1]
      }
    });
    
    console.log('[DailyTrend] loadChartData - API response received:', response.data);
    chartData.value = response.data;
    renderChart();
  } catch (err) {
    console.error('[DailyTrend] loadChartData - Error during API call:', err);
    error.value = true;
    
    if (err.response && err.response.status === 401) {
      console.warn('[DailyTrend] loadChartData - Received 401, logging out and redirecting.');
      errorMessage.value = '登录状态已失效，请重新登录。';
      userStore.logout();
    } else {
      errorMessage.value = err.response 
        ? `错误 ${err.response.status}: ${err.response.data?.detail || err.response.statusText || '无法连接到服务器'}` 
        : `网络请求错误: ${err.message || '未知网络错误'}`;
      ElMessage.error(errorMessage.value || '加载每日趋势数据失败，请稍后再试。');
    }
  } finally {
    chartLoading.value = false;
    console.log('[DailyTrend] loadChartData - Finished. chartLoading:', chartLoading.value, 'error:', error.value);
  }
};

// 渲染图表
const renderChart = () => {
  if (!chartData.value || chartData.value.length === 0) {
    console.warn('[DailyTrend] renderChart - No data to render');
    return;
  }
  
  // 确保DOM已渲染
  setTimeout(() => {
    const chartDom = document.getElementById('dailyTrendChart');
    if (!chartDom) {
      console.warn('[DailyTrend] renderChart - Chart DOM element not found');
      return;
    }
    
    // 如果图表已存在，先销毁
    if (chart) {
      chart.dispose();
    }
    
    chart = echarts.init(chartDom);
    
    try {
      // 确保日期格式正确
      const dates = chartData.value.map(item => {
        if (typeof item.date === 'string') {
          return item.date;
        } else if (item.date instanceof Date) {
          return item.date.toISOString().split('T')[0];
        }
        return String(item.date);
      });
      
      const incomeData = chartData.value.map(item => Number(item.total_income || 0));
      const expenseData = chartData.value.map(item => Number(item.total_expense || 0));
      const balanceData = chartData.value.map(item => Number(item.balance || 0));
      
      console.log('[DailyTrend] renderChart - Processed data:', { 
        dates, 
        incomeData, 
        expenseData, 
        balanceData 
      });
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          }
        },
        legend: {
          data: ['收入', '支出', '结余']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: [
          {
            type: 'category',
            boundaryGap: false,
            data: dates
          }
        ],
        yAxis: [
          {
            type: 'value'
          }
        ],
        series: [
          {
            name: '收入',
            type: 'line',
            stack: 'Total',
            areaStyle: {},
            emphasis: {
              focus: 'series'
            },
            data: incomeData,
            itemStyle: {
              color: '#67C23A'
            }
          },
          {
            name: '支出',
            type: 'line',
            stack: 'Total',
            areaStyle: {},
            emphasis: {
              focus: 'series'
            },
            data: expenseData,
            itemStyle: {
              color: '#F56C6C'
            }
          },
          {
            name: '结余',
            type: 'line',
            emphasis: {
              focus: 'series'
            },
            data: balanceData,
            itemStyle: {
              color: '#409EFF'
            }
          }
        ]
      };
      
      chart.setOption(option);
      console.log('[DailyTrend] renderChart - Chart rendered successfully');
    } catch (err) {
      console.error('[DailyTrend] renderChart - Error rendering chart:', err);
      error.value = true;
      errorMessage.value = '渲染图表时出错: ' + (err.message || '未知错误');
    }
    
    // 添加窗口大小变化时重绘图表
    window.addEventListener('resize', () => {
      chart && chart.resize();
    });
  }, 0);
};

// 初始化认证和加载数据
const initializeAuthAndLoad = async () => {
  authLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  console.log('[DailyTrend] initializeAuthAndLoad - Start. Initial authLoading:', authLoading.value);
  
  try {
    // 先检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[DailyTrend] initializeAuthAndLoad - No token found. User needs to login.');
      errorMessage.value = '您尚未登录，请先登录以访问报表。';
      error.value = true;
      return;
    }
    
    // 确保token在两个存储位置都存在
    if (sessionToken && !localToken && localStorage.getItem('rememberMe') === 'true') {
      localStorage.setItem('token', sessionToken);
    } else if (localToken && !sessionToken) {
      sessionStorage.setItem('token', localToken);
    }
    
    // 强制在每个请求前重新验证用户身份
    try {
      console.log('[DailyTrend] initializeAuthAndLoad - Attempting to verify authentication');
      await userStore.checkAuth();
      console.log('[DailyTrend] initializeAuthAndLoad - Auth check completed. User logged in:', userStore.isLoggedIn);

      if (!userStore.isLoggedIn) {
        console.warn('[DailyTrend] User not authenticated after checkAuth');
        errorMessage.value = '认证失败，请重新登录。';
        error.value = true;
        return;
      }
    } catch (authError) {
      console.error('[DailyTrend] Authentication error:', authError);
      errorMessage.value = '认证失败，请重新登录。';
      error.value = true;
      return;
    }

    console.log('[DailyTrend] Loading data after successful authentication check');
    
    // 加载图表数据
      if (props.dateRange && props.dateRange.length === 2) {
        await loadChartData(props.dateRange);
      } else {
        console.warn('[DailyTrend] initializeAuthAndLoad - Date range not ready for initial load.');
      }
  } catch (error) {
    console.error('[DailyTrend] Error in initializeAuthAndLoad:', error);
    errorMessage.value = `加载失败: ${error.message || '未知错误'}`;
    error.value = true;
  } finally {
    console.log('[DailyTrend] initializeAuthAndLoad completed');
    authLoading.value = false;
  }
};

// 组件挂载和卸载时的清理
onMounted(() => {
  console.log('[DailyTrend] Component mounted. Initial dateRange:', props.dateRange);
  initializeAuthAndLoad();
});

onUnmounted(() => {
  // 销毁图表实例
  if (chart) {
    chart.dispose();
    chart = null;
  }
  
  // 移除事件监听
  window.removeEventListener('resize', () => {
    chart && chart.resize();
  });
});
</script>

<style scoped>
.daily-trend {
  height: 100%;
}

.chart-container {
  background-color: #fff;
  border-radius: 4px;
  padding: 15px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 15px;
}

.chart-header h3 {
  margin: 0;
  color: #303133;
  font-weight: 500;
}

.chart-content {
  flex-grow: 1;
  position: relative;
}

.chart-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.chart {
  width: 100%;
  height: 100%;
}

.loading-overlay, .error-message {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 20px;
}

.error-message .el-alert {
  margin-bottom: 20px;
}

.mt-4 {
  margin-top: 16px;
}
</style> 