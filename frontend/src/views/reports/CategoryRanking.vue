<template>
  <div class="category-ranking">
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
      <div class="mint-pie-chart-container">
        <div class="mint-pie-chart-header">
          <h3>{{ transactionType === 'expense' ? '支出' : '收入' }}类别饼图</h3>
          <div class="chart-actions">
            <el-radio-group v-model="transactionType" size="small" class="mint-radio-group">
              <el-radio-button label="expense">支出</el-radio-button>
              <el-radio-button label="income">收入</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="mint-pie-chart-content">
          <div v-if="chartLoading" class="chart-placeholder">
            <el-empty description="正在加载饼图..." />
          </div>
          <div v-else-if="rankingData.length === 0" class="chart-placeholder">
            <el-empty description="没有找到数据呢 (˘･_･˘)" />
          </div>
          <div v-else id="mintPieChart" class="mint-chart"></div>
        </div>
      </div>
      
      <div class="ranking-table">
        <h3>{{ transactionType === 'expense' ? '支出' : '收入' }}分类排行</h3>
        <el-table v-loading="chartLoading" :data="rankingData" stripe style="width: 100%">
          <el-table-column prop="rank" label="排名" width="80" />
          <el-table-column prop="category" label="分类" />
          <el-table-column prop="amount" label="金额" />
          <el-table-column prop="percentage" label="占比">
            <template #default="scope">
              <div class="percentage-bar">
                <div 
                  class="percentage-fill" 
                  :style="{ width: scope.row.percentage, backgroundColor: getCategoryColor(scope.row.category) }"
                ></div>
                <span>{{ scope.row.percentage }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
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

const transactionType = ref('expense');
const rankingData = ref([]);
const loading = ref(false);
const chartLoading = ref(false);
const error = ref(false);
const errorMessage = ref('');
const authLoading = ref(true);
let chart = null;

// 为不同的分类生成不同的颜色
const categoryColors = {
  '餐饮美食': '#FF6B6B', // 鲜红色
  '交通出行': '#FFD93D', // 明黄色
  '服饰美容': '#6BCB77', // 翠绿色
  '日用百货': '#4D96FF', // 亮蓝色
  '住房物业': '#9B59B6', // 紫色
  '医疗健康': '#2ECC71', // 绿色
  '文教娱乐': '#FF9671', // 橙色
  '人情往来': '#FFC75F', // 金黄色
  '工资薪酬': '#43AA8B', // 青绿色
  '投资理财': '#277DA1', // 深蓝色
  '其他收入': '#F94892', // 粉红色
  '其他支出': '#90BE6D', // 嫩绿色
  '未分类': '#98C1D9'    // 灰蓝色
};

const getCategoryColor = (category) => {
  return categoryColors[category] || '#909399';
};

// 去登录页
const goToLogin = () => {
  router.push({ name: 'login', query: { redirect: window.location.pathname + window.location.search } });
};

// 重试加载数据
const retryLoading = () => {
  initializeAuthAndLoad();
};

// 监听日期范围和交易类型变化
watch(
  [() => props.dateRange, transactionType],
  ([newDateRange, newType], [oldDateRange, oldType]) => {
    console.log('[CategoryRanking] dateRange or type changed:', { newDateRange, newType, oldDateRange, oldType });
    
    // 防止初始化时重复加载
    if (authLoading.value) {
      console.log('[CategoryRanking] Skipping watcher during auth loading');
      return;
    }
    
    if (newDateRange && newDateRange.length === 2 && 
        (JSON.stringify(newDateRange) !== JSON.stringify(oldDateRange) || newType !== oldType)) {
      console.log('[CategoryRanking] Loading data due to dateRange or type change');
      loadRankingData(newDateRange, newType);
    }
  }
);

// 加载排行数据
const loadRankingData = async (dateRange, type) => {
  console.log('[CategoryRanking] loadRankingData - Start. Type:', type, 'Date range:', dateRange);
  chartLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  
  try {
    // 检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[CategoryRanking] loadRankingData: No token found. Aborting.');
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
      console.log('[CategoryRanking] loadRankingData: Token exists but user not logged in. Attempting to restore session...');
      try {
        await userStore.checkAuth();
        if (!userStore.isLoggedIn) {
          console.warn('[CategoryRanking] loadRankingData: Failed to restore session.');
          error.value = true;
          errorMessage.value = '您的登录已失效，请重新登录。';
          return;
        }
      } catch (err) {
        console.error('[CategoryRanking] loadRankingData: Error restoring session:', err);
        error.value = true;
        errorMessage.value = '恢复会话失败，请重新登录。';
        return;
      }
    }
    
    console.log('[CategoryRanking] loadRankingData - Making API request');
    const response = await apiInstance.get('/reports/category-ranking', {
      params: {
        transaction_type: type,
        start_date: dateRange[0],
        end_date: dateRange[1]
      }
    });
    
    console.log('[CategoryRanking] loadRankingData - API response received:', response.data);
    
    // 处理API返回的数据
    const data = response.data;
    rankingData.value = data.map((item, index) => ({
      rank: index + 1,
      category: item.category,
      amount: `¥ ${item.total_amount.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`,
      percentage: `${item.percentage}%`,
      rawPercentage: item.percentage, // 保存原始百分比值用于图表
      rawAmount: item.total_amount // 保存原始金额用于图表
    }));
    
    renderPieChart();
  } catch (err) {
    console.error('[CategoryRanking] loadRankingData - Error during API call:', err);
    error.value = true;
    
    if (err.response && err.response.status === 401) {
      console.warn('[CategoryRanking] loadRankingData - Received 401, logging out and redirecting.');
      errorMessage.value = '登录状态已失效，请重新登录。';
      userStore.logout();
    } else {
      errorMessage.value = err.response 
        ? `错误 ${err.response.status}: ${err.response.data?.detail || err.response.statusText || '无法连接到服务器'}` 
        : `网络请求错误: ${err.message || '未知网络错误'}`;
      ElMessage.error(errorMessage.value || '加载分类排行数据失败，请稍后再试。');
    }
  } finally {
    chartLoading.value = false;
    console.log('[CategoryRanking] loadRankingData - Finished. chartLoading:', chartLoading.value, 'error:', error.value);
  }
};

// 渲染饼图
const renderPieChart = () => {
  if (!rankingData.value || rankingData.value.length === 0) return;
  
  // 确保DOM已渲染
  setTimeout(() => {
    const mintPieChartDom = document.getElementById('mintPieChart');
    
    if (!mintPieChartDom) {
      console.warn('[CategoryRanking] renderPieChart - Mint chart DOM element not found');
      return;
    }
    
    // 如果图表已存在，先销毁
    if (chart) {
      chart.dispose();
    }
    
    // 初始化薄荷绿风格饼图
    chart = echarts.init(mintPieChartDom);
    
    // 优化数据处理，对于小于1%的部分进行合并
    const MIN_PERCENTAGE = 3.0; // 最小百分比阈值
    const originalData = rankingData.value.map(item => ({
      name: item.category,
      value: item.rawAmount,
      percentage: item.rawPercentage
    }));
    
    // 分离大于和小于阈值的数据项
    const mainData = [];
    const smallData = [];
    
    originalData.forEach(item => {
      if (item.percentage >= MIN_PERCENTAGE) {
        mainData.push(item);
      } else {
        smallData.push(item);
      }
    });
    
    // 如果有小于阈值的项，合并为"其他"
    let pieData = [...mainData];
    if (smallData.length > 0) {
      const otherValue = smallData.reduce((sum, item) => sum + item.value, 0);
      const otherPercentage = smallData.reduce((sum, item) => sum + item.percentage, 0);
      const smallCategoriesList = smallData.map(item => item.name).join(', ');
      
      console.log(`[CategoryRanking] 合并了 ${smallData.length} 个小分类: ${smallCategoriesList}`);
      
      if (otherValue > 0) {
        pieData.push({
          name: `其他 (${smallData.length}项)`,
          value: otherValue,
          percentage: otherPercentage,
          // 鼠标悬停时的提示文本
          tooltip: {
            formatter: function(params) {
              return `<div style="font-weight:bold;margin-bottom:5px;">其他 (${smallData.length}项): ${otherValue.toFixed(2)} (${otherPercentage.toFixed(2)}%)</div>` + 
                     smallData.map(item => 
                       `${item.name}: ${item.value.toFixed(2)} (${item.percentage.toFixed(2)}%)`
                     ).join('<br/>');
            }
          }
        });
      }
    }
    
    // 优化数据排序，让"其他"类别显示在最后
    pieData.sort((a, b) => {
      if (a.name.startsWith('其他')) return 1;
      if (b.name.startsWith('其他')) return -1;
      return b.value - a.value;
    });
    
    // 薄荷绿风格饼图配置
    const mintOption = {
      tooltip: {
        trigger: 'item',
        formatter: function(params) {
          // 如果数据项有自定义tooltip
          if (params.data.tooltip) {
            return params.data.tooltip.formatter(params);
          }
          // 默认tooltip格式
          return `${params.name}: ${params.value.toFixed(2)} (${params.percent}%)`;
        },
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderColor: '#8CDAB6',
        borderWidth: 2,
        padding: [8, 12],
        textStyle: {
          color: '#3D6E59'
        }
      },
      legend: {
        type: 'scroll',
        icon: 'circle',
        bottom: '5%',
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 10,
        textStyle: {
          fontSize: 12,
          color: '#3D6E59'
        }
      },
      series: [
        {
          name: transactionType.value === 'expense' ? '支出' : '收入',
          type: 'pie',
          radius: '65%',
          center: ['50%', '40%'],
          data: pieData,
          minShowLabelAngle: 5, // 最小显示标签的角度
          avoidLabelOverlap: true,
          label: {
            formatter: '{b}: {d}%',
            fontSize: 12,
            fontWeight: 'normal',
            color: '#3D6E59',
            position: 'outside',
            alignTo: 'labelLine',
            // 只显示占比超过5%的标签
            show: function(params) {
              return params.percent > 5;
            }
          },
          labelLine: {
            length: 10,
            length2: 8,
            smooth: true,
            lineStyle: {
              width: 1,
              type: 'solid'
            }
          },
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2,
            color: function(params) {
              // 使用更鲜艳的颜色
              const mintCategoryColors = {
                '餐饮美食': '#FF6B6B', // 鲜红色
                '交通出行': '#FFD93D', // 明黄色
                '服饰美容': '#6BCB77', // 翠绿色
                '日用百货': '#4D96FF', // 亮蓝色
                '住房物业': '#9B59B6', // 紫色
                '医疗健康': '#2ECC71', // 绿色
                '文教娱乐': '#FF9671', // 橙色
                '人情往来': '#FFC75F', // 金黄色
                '工资薪酬': '#43AA8B', // 青绿色
                '投资理财': '#277DA1', // 深蓝色
                '其他收入': '#F94892', // 粉红色
                '其他支出': '#90BE6D', // 嫩绿色
                '未分类': '#98C1D9',   // 灰蓝色
              };
              
              // 如果是"其他"类别，使用特定颜色
              if (params.name.startsWith('其他')) {
                return '#B8B8B8'; // 灰色
              }
              
              return mintCategoryColors[params.name] || '#A7E0C7';
            },
            shadowBlur: 5,
            shadowColor: 'rgba(0, 0, 0, 0.1)'
          },
          animationType: 'scale',
          animationEasing: 'elasticOut',
          emphasis: {
            focus: 'self',
            scaleSize: 10,
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            }
          }
        }
      ]
    };
    
    chart.setOption(mintOption);
    
    // 添加窗口大小变化时重绘图表
    window.addEventListener('resize', () => {
      chart && chart.resize();
    });
    
    console.log('[CategoryRanking] renderPieChart - Chart rendered successfully');
  }, 0);
};

// 初始化认证和加载数据
const initializeAuthAndLoad = async () => {
  authLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  console.log('[CategoryRanking] initializeAuthAndLoad - Start. Initial authLoading:', authLoading.value);
  
  try {
    // 先检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[CategoryRanking] initializeAuthAndLoad - No token found. User needs to login.');
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
    
    if (!userStore.isLoggedIn) {
      console.log('[CategoryRanking] initializeAuthAndLoad - User not logged in, attempting to fetch user info via checkAuth.');
      await userStore.checkAuth();
      console.log('[CategoryRanking] initializeAuthAndLoad - checkAuth completed. User info:', userStore.user);
    }

    if (userStore.isLoggedIn && userStore.user) {
      console.log('[CategoryRanking] initializeAuthAndLoad - Auth check successful. User:', userStore.user.username, 'Proceeding to load data.');
      if (props.dateRange && props.dateRange.length === 2) {
        await loadRankingData(props.dateRange, transactionType.value);
      } else {
        console.warn('[CategoryRanking] initializeAuthAndLoad - Date range not ready for initial load.');
      }
    } else {
      console.warn('[CategoryRanking] initializeAuthAndLoad - Auth check failed or user not logged in.');
      errorMessage.value = '您的登录已过期或无效，请重新登录。';
      error.value = true;
    }
  } catch (err) {
    console.error('[CategoryRanking] initializeAuthAndLoad - Error during auth check or initial load:', err);
    errorMessage.value = '检查登录状态时发生错误，请刷新页面或重新登录。';
    error.value = true;
  } finally {
    authLoading.value = false;
    console.log('[CategoryRanking] initializeAuthAndLoad - Finished. authLoading:', authLoading.value, 'error:', error.value);
  }
};

// 组件挂载和卸载时的清理
onMounted(() => {
  console.log('[CategoryRanking] Component mounted. Initial dateRange:', props.dateRange);
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
.category-ranking {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background-color: #E3F2ED;
  padding: 15px;
  border-radius: 18px;
}

/* 薄荷绿风格饼图容器 */
.mint-pie-chart-container {
  background-color: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px solid #A7E0C7;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.mint-pie-chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.mint-pie-chart-header h3 {
  margin: 0;
  color: #3D6E59;
  font-weight: 500;
  font-size: 18px;
}

.mint-pie-chart-content {
  flex-grow: 1;
  position: relative;
  min-height: 300px;
}

.mint-chart {
  width: 100%;
  height: 100%;
}

.mint-radio-group :deep(.el-radio-button__inner) {
  border-radius: 14px;
  border: 1px solid #8CDAB6;
  background-color: #F0FBF7;
  color: #3D6E59;
  font-size: 14px;
  transition: all 0.3s ease;
}

.mint-radio-group :deep(.el-radio-button__original) {
  opacity: 0;
}

.mint-radio-group :deep(.el-radio-button__inner:hover) {
  color: #2A4D3E;
  background-color: #C6F7E2;
}

.mint-radio-group :deep(.el-radio-button.is-active .el-radio-button__inner) {
  background-color: #5DAF8E;
  border-color: #5DAF8E;
  color: white;
  box-shadow: 0 0 8px rgba(93, 175, 142, 0.5);
}

/* 修改其他容器样式以匹配薄荷绿风格 */
.chart-container {
  background-color: #fff;
  border-radius: 16px;
  padding: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px solid #A7E0C7;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.chart-header h3 {
  margin: 0;
  color: #3D6E59;
  font-weight: 500;
  font-size: 16px;
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

.ranking-table {
  background-color: #fff;
  border-radius: 16px;
  padding: 15px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px solid #A7E0C7;
}

.ranking-table h3 {
  margin: 0 0 15px 0;
  color: #3D6E59;
  font-weight: 500;
  font-size: 16px;
}

/* 美化表格样式 */
:deep(.el-table) {
  border-radius: 12px !important;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: #E8F6F0 !important;
  color: #3D6E59;
  font-weight: normal;
}

:deep(.el-table td) {
  color: #4E6E61;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #F0FBF7;
}

:deep(.el-table__body tr:hover > td) {
  background-color: #C6F7E2 !important;
}

.percentage-bar {
  display: flex;
  align-items: center;
  width: 100%;
  height: 20px;
  background-color: #F0FBF7;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  border: 1px solid #A7E0C7;
}

.percentage-fill {
  height: 100%;
  border-radius: 10px;
}

.percentage-bar span {
  position: absolute;
  right: 10px;
  font-size: 12px;
  color: #3D6E59;
}

.chart {
  width: 100%;
  height: 100%;
}

/* 加载和错误状态的薄荷绿风格 */
.loading-overlay, .error-message {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 20px;
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px dashed #8CDAB6;
}

.error-message .el-alert {
  margin-bottom: 20px;
  border-radius: 8px;
}

:deep(.el-button) {
  border-radius: 20px;
  font-size: 14px;
  padding: 8px 20px;
}

:deep(.el-button--primary) {
  background-color: #5DAF8E;
  border-color: #5DAF8E;
}

:deep(.el-button--primary:hover) {
  background-color: #3D6E59;
  border-color: #3D6E59;
}

.mt-4 {
  margin-top: 16px;
}

/* 修改空状态提示的样式 */
:deep(.el-empty__description) {
  color: #3D6E59;
  font-size: 14px;
}

:deep(.el-empty__image) {
  opacity: 0.7;
}
</style> 