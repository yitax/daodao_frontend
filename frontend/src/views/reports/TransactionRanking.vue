<template>
  <div class="transaction-ranking">
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
      <div class="filter-container">
        <div class="date-picker">
          <el-date-picker
            v-model="localDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
          />
        </div>

        <div class="filter-btns">
          <el-button
            @click="setDateRange('today')"
            :class="{ active: activeRange === 'today' }"
            >今天</el-button
          >
          <el-button
            @click="setDateRange('week')"
            :class="{ active: activeRange === 'week' }"
            >本周</el-button
          >
          <el-button
            @click="setDateRange('month')"
            :class="{ active: activeRange === 'month' }"
            >本月</el-button
          >
          <el-button
            @click="setDateRange('year')"
            :class="{ active: activeRange === 'year' }"
            >今年</el-button
          >
        </div>

        <div class="type-tabs">
          <el-button
            @click="changeType('expense')"
            :class="{ active: currentType === 'expense' }"
            >支出</el-button
          >
          <el-button
            @click="changeType('income')"
            :class="{ active: currentType === 'income' }"
            >收入</el-button
          >
        </div>
      </div>
      
      <!-- 排序选择器 -->
      <div class="sort-container">
        <span class="sort-label">排序方式:</span>
        <div class="sort-options">
          <el-button
            size="small"
            @click="changeSortBy('amount')"
            :class="{ active: sortBy === 'amount' }"
          >按金额排序</el-button>
          <el-button
            size="small"
            @click="changeSortBy('date')"
            :class="{ active: sortBy === 'date' }"
          >按日期排序</el-button>
        </div>
      </div>

      <div class="ranking-list">
        <el-table v-loading="chartLoading" :data="rankingData" stripe style="width: 100%" :header-cell-style="headerStyle" :row-class-name="getRowClassName">
          <el-table-column prop="ranking" label="排名" width="80" />
          <el-table-column prop="date" label="日期" width="120">
            <template #default="scope">
              {{ formatDate(scope.row.date) }}
            </template>
          </el-table-column>
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="category" label="分类" width="120">
            <template #default="scope">
              <el-tag :style="{ backgroundColor: getCategoryColor(scope.row.category) }" class="category-tag">
                {{ scope.row.category }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="scope">
              <span :class="{ 'income-amount': scope.row.is_income, 'expense-amount': !scope.row.is_income }">
                {{ formatAmount(scope.row.amount) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="total > 10" class="pagination">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="10"
          :current-page="currentPage"
          @current-change="handlePageChange"
        />
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue';
import axios from 'axios';
import { ElMessage, ElSkeleton, ElAlert, ElButton } from 'element-plus';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../store/user';
import { getStartOfToday, getStartOfThisWeek, getStartOfThisMonth, getStartOfThisYear } from '@/utils/dateUtils';
import dayjs from 'dayjs';

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
    default: () => []
  }
});

// 定义事件
const emit = defineEmits(['update:dateRange']);

// 创建本地日期范围变量
const localDateRange = ref([]);

// 监听props.dateRange的变化，更新本地变量
watch(() => props.dateRange, (newDateRange) => {
  if (newDateRange && Array.isArray(newDateRange) && newDateRange.length === 2) {
    localDateRange.value = [...newDateRange];
  }
}, { immediate: true });

// 处理本地日期范围变化
const handleDateRangeChange = (newValue) => {
  console.log('Date range changed:', newValue);
  emit('update:dateRange', newValue);
  loadRankingData(newValue);
};

const transactionType = ref('expense');
const sortBy = ref('amount');
const currentPage = ref(1);
const total = ref(0);
const loading = ref(false);
const chartLoading = ref(false);
const error = ref(false);
const errorMessage = ref('');
const authLoading = ref(true);
const rankingData = ref([]);
const selectedCategory = ref('');
const expenseCategories = ref([]);
const incomeCategories = ref([]);
const activeRange = ref('month');
const currentType = ref('expense');

// 去登录页
const goToLogin = () => {
  router.push({ name: 'login', query: { redirect: window.location.pathname + window.location.search } });
};

// 重试加载数据
const retryLoading = () => {
  initializeAuthAndLoad();
};

// 获取标签类型
const getTagType = (category) => {
  const tagTypes = {
    '餐饮美食': 'danger',    // 红色
    '交通出行': 'warning',   // 黄色
    '服饰美容': 'success',   // 绿色
    '日用百货': 'info',      // 蓝色
    '住房物业': 'purple',    // 紫色
    '医疗健康': 'success',   // 绿色
    '文教娱乐': 'orange',    // 橙色
    '人情往来': 'gold',      // 金黄色
    '工资薪酬': 'teal',      // 青绿色
    '投资理财': 'primary',   // 深蓝色
    '其他收入': 'pink',      // 粉红色
    '其他支出': 'lime',      // 嫩绿色
    '未分类': ''             // 默认
  };
  return tagTypes[category] || '';
};

// 初始化分类
const initializeCategories = () => {
  // 支出分类列表
  expenseCategories.value = [
    '餐饮美食', '交通出行', '服饰美容', '日用百货',
    '住房物业', '医疗健康', '文教娱乐', '人情往来', '其他支出'
  ];
  
  // 收入分类列表
  incomeCategories.value = [
    '工资薪酬', '投资理财', '其他收入'
  ];
};

// 监听筛选条件变化
watch(
  [() => props.dateRange, transactionType, sortBy, selectedCategory],
  ([newDateRange, newType, newSort, newCategory], [oldDateRange, oldType, oldSort, oldCategory]) => {
    console.log('[TransactionRanking] Filter changed:', { 
      dateRange: { new: newDateRange, old: oldDateRange },
      type: { new: newType, old: oldType },
      sort: { new: newSort, old: oldSort },
      category: { new: newCategory, old: oldCategory }
    });
    
    // 防止初始化时重复加载
    if (authLoading.value) {
      console.log('[TransactionRanking] Skipping watcher during auth loading');
      return;
    }
    
    if (newDateRange && newDateRange.length === 2 && 
        (JSON.stringify(newDateRange) !== JSON.stringify(oldDateRange) || 
         newType !== oldType || 
         newSort !== oldSort ||
         newCategory !== oldCategory)) {
      console.log('[TransactionRanking] Loading data due to filter change');
      currentPage.value = 1;
      loadRankingData(newDateRange, newType, newSort, currentPage.value, newCategory);
    }
  }
);

// 加载排行数据
const loadRankingData = async (dateRange, type, sort, page, category) => {
  // 参数处理，确保有默认值
  const currentDateRange = dateRange || localDateRange.value;
  const currentType = type || transactionType.value;
  const currentSort = sort || sortBy.value;
  const currentPage = page || 1;
  const currentCategory = category !== undefined ? category : selectedCategory.value;

  console.log('[TransactionRanking] loadRankingData - Start. Params:', {
    dateRange: currentDateRange,
    type: currentType, 
    sort: currentSort, 
    page: currentPage, 
    category: currentCategory
  });

  if (!currentDateRange || !Array.isArray(currentDateRange) || currentDateRange.length < 2) {
    console.error('[TransactionRanking] loadRankingData - Invalid date range:', currentDateRange);
    error.value = true;
    errorMessage.value = '日期范围无效，无法加载数据';
    return;
  }

  if (!currentType) {
    console.error('[TransactionRanking] loadRankingData - Missing transaction type');
    error.value = true;
    errorMessage.value = '请选择交易类型（收入或支出）';
    return;
  }

  chartLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  
  try {
    // 检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[TransactionRanking] loadRankingData: No token found. Aborting.');
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
      console.log('[TransactionRanking] loadRankingData: Token exists but user not logged in. Attempting to restore session...');
      try {
        console.log('[TransactionRanking] initializeAuthAndLoad - Attempting to verify authentication');
        await userStore.checkAuth();
        console.log('[TransactionRanking] initializeAuthAndLoad - Auth check completed. User logged in:', userStore.isLoggedIn);
        
        if (!userStore.isLoggedIn) {
          console.warn('[TransactionRanking] User not authenticated after checkAuth');
          errorMessage.value = '认证失败，请重新登录。';
          error.value = true;
          return;
        }
      } catch (authError) {
        console.error('[TransactionRanking] Authentication error:', authError);
        errorMessage.value = '认证失败，请重新登录。';
        error.value = true;
        return;
      }
    }
    
    console.log('[TransactionRanking] loadRankingData - Making API request');
    const params = {
      transaction_type: currentType,
      start_date: currentDateRange[0],
      end_date: currentDateRange[1],
      limit: 20
    };
    
    // 添加分类筛选
    if (currentCategory) {
      params.category = currentCategory;
    }
    
    console.log('[TransactionRanking] API request params:', params);
    const response = await apiInstance.get('/reports/transaction-ranking', { params });
    
    console.log('[TransactionRanking] loadRankingData - API response received:', response.data);
    
    // 处理返回的数据
    const transactions = response.data;
    
    // 添加检查确保transactions是数组
    if (!Array.isArray(transactions)) {
      console.error('[TransactionRanking] API返回的数据不是数组:', transactions);
      error.value = true;
      errorMessage.value = 'API返回格式错误，请联系管理员';
      rankingData.value = [];
      return;
    }
    
    total.value = transactions.length;
    
    // 调试输出各个交易的原始金额
    transactions.forEach((tx, idx) => {
      console.log(`[TransactionRanking] Transaction #${idx+1} amount:`, tx.amount, typeof tx.amount);
    });
    
    // 根据排序类型处理数据 - 日期或金额
    let sortedData;
    if (currentSort === 'date') {
      console.log('[TransactionRanking] Sorting by date');
      sortedData = [...transactions].sort((a, b) => {
        // 安全地处理日期比较
        const dateA = a.date ? new Date(a.date) : new Date(0);
        const dateB = b.date ? new Date(b.date) : new Date(0);
        return dateB - dateA;
      });
    } else {
      console.log('[TransactionRanking] Sorting by amount');
      // 按金额排序，先把数据转为数字确保比较正确
      sortedData = [...transactions].sort((a, b) => {
        // 确保正确转换为数字进行比较
        const amountA = parseFloat(a.amount) || 0;
        const amountB = parseFloat(b.amount) || 0;
        return amountB - amountA;
      });
    }
    
    // 格式化数据，安全处理每个字段
    rankingData.value = sortedData.map((item, index) => {
      // 确保所有必要字段存在
      const safeItem = {
        id: item?.id,
        date: item?.date || '未知日期',
        description: item?.description || '无描述',
        category: item?.category || '未分类',
        amount: item?.amount,
        transaction_type: item?.transaction_type || currentType
      };
      
      // 确保日期格式正确
      let formattedDate = safeItem.date;
      if (formattedDate instanceof Date) {
        formattedDate = formattedDate.toISOString().split('T')[0];
      } else if (typeof formattedDate === 'string') {
        // 保留字符串日期，不做处理
      } else {
        formattedDate = '日期格式错误';
      }
      
      // 对金额进行安全处理
      let amountValue = 0;
      if (safeItem.amount !== undefined && safeItem.amount !== null) {
        // 尝试确保它是一个有效的数字
        amountValue = parseFloat(safeItem.amount);
        if (isNaN(amountValue)) {
          console.error(`[TransactionRanking] Invalid amount for transaction ${safeItem.id}:`, safeItem.amount);
          amountValue = 0;
        }
      }
      
      // 格式化金额显示
      const formattedAmount = amountValue.toFixed(2); // 确保两位小数
      
      return {
        ranking: index + 1,
        id: safeItem.id,
        date: formattedDate,
        description: safeItem.description,
        category: safeItem.category,
        rawAmount: amountValue, // 保存原始数值用于排序
        amount: formattedAmount, // 格式化后的金额用于显示
        is_income: safeItem.transaction_type === 'income'
      };
    });
    
    if (rankingData.value.length === 0) {
      console.log('[TransactionRanking] No data returned from API');
    }
    
  } catch (err) {
    console.error('[TransactionRanking] loadRankingData - Error during API call:', err);
    error.value = true;
    
    if (err.response && err.response.status === 401) {
      console.warn('[TransactionRanking] loadRankingData - Received 401, logging out and redirecting.');
      errorMessage.value = '登录状态已失效，请重新登录。';
      userStore.logout();
    } else {
      errorMessage.value = err.response 
        ? `网络请求错误: ${err.response.status}: ${err.response.data?.detail || err.response.statusText || '无法连接到服务器'}` 
        : `网络请求错误: ${err.message || '未知网络错误'}`;
      ElMessage.error('加载明细排行数据失败，请稍后再试。');
    }
    
    rankingData.value = [];
  } finally {
    chartLoading.value = false;
    console.log('[TransactionRanking] loadRankingData - Finished. chartLoading:', chartLoading.value, 'error:', error.value);
  }
};

// 处理页码变化
const handlePageChange = (page) => {
  console.log('[TransactionRanking] Page changed to:', page);
  currentPage.value = page;
  loadRankingData(localDateRange.value, transactionType.value, sortBy.value, page, selectedCategory.value);
};

// 初始化认证和加载数据
const initializeAuthAndLoad = async () => {
  authLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  console.log('[TransactionRanking] initializeAuthAndLoad - Start. Initial authLoading:', authLoading.value);
  
  try {
    // 先检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[TransactionRanking] initializeAuthAndLoad - No token found. User needs to login.');
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
      console.log('[TransactionRanking] initializeAuthAndLoad - Attempting to verify authentication');
      await userStore.checkAuth();
      console.log('[TransactionRanking] initializeAuthAndLoad - Auth check completed. User logged in:', userStore.isLoggedIn);
      
      if (!userStore.isLoggedIn) {
        console.warn('[TransactionRanking] User not authenticated after checkAuth');
        errorMessage.value = '认证失败，请重新登录。';
        error.value = true;
        return;
      }
    } catch (authError) {
      console.error('[TransactionRanking] Authentication error:', authError);
      errorMessage.value = '认证失败，请重新登录。';
      error.value = true;
      return;
    }

    console.log('[TransactionRanking] Loading data after successful authentication check');
    
    // 加载交易排行数据
    if (localDateRange.value && localDateRange.value.length === 2 && transactionType.value) {
      await loadRankingData(localDateRange.value, transactionType.value, sortBy.value, currentPage.value, selectedCategory.value);
    } else {
      console.warn('[TransactionRanking] initializeAuthAndLoad - Parameters not ready for initial load.');
    }
  } catch (error) {
    console.error('[TransactionRanking] Error in initializeAuthAndLoad:', error);
    errorMessage.value = `加载失败: ${error.message || '未知错误'}`;
    error.value = true;
  } finally {
    console.log('[TransactionRanking] initializeAuthAndLoad completed');
    authLoading.value = false;
  }
};

// 组件挂载时初始化
onMounted(() => {
  console.log('[TransactionRanking] Component mounted. Initial dateRange:', props.dateRange);
  initializeCategories();
  
  // 如果从props接收的dateRange无效，则设置默认日期范围（本月）
  if (!props.dateRange || !Array.isArray(props.dateRange) || props.dateRange.length !== 2) {
    setDateRange('month');
  } else {
    // 使用props.dateRange的值初始化本地日期范围
    localDateRange.value = [...props.dateRange];
  }
  
  initializeAuthAndLoad();
});

// 处理类别变化
const handleCategoryChange = () => {
  console.log('[TransactionRanking] Category changed to:', selectedCategory.value);
  currentPage.value = 1;
  loadRankingData(localDateRange.value, transactionType.value, sortBy.value, currentPage.value, selectedCategory.value);
};

// 设置日期范围
const setDateRange = (range) => {
  activeRange.value = range;
  const today = new Date();
  let newDateRange = [];

  switch (range) {
    case 'today': {
      const todayStr = dayjs(today).format('YYYY-MM-DD');
      newDateRange = [todayStr, todayStr];
      console.log(`Today range: ${newDateRange[0]} to ${newDateRange[1]}`);
      break;
    }
    case 'week': {
      const startOfWeek = getStartOfThisWeek();
      const startStr = dayjs(startOfWeek).format('YYYY-MM-DD');
      const todayStr = dayjs(today).format('YYYY-MM-DD');
      newDateRange = [startStr, todayStr];
      console.log(`Week range: ${newDateRange[0]} to ${newDateRange[1]}`);
      break;
    }
    case 'month': {
      const startOfMonth = getStartOfThisMonth();
      const startStr = dayjs(startOfMonth).format('YYYY-MM-DD');
      const todayStr = dayjs(today).format('YYYY-MM-DD');
      newDateRange = [startStr, todayStr];
      console.log(`Month range: ${newDateRange[0]} to ${newDateRange[1]}`);
      break;
    }
    case 'year': {
      const startOfYear = getStartOfThisYear();
      const startStr = dayjs(startOfYear).format('YYYY-MM-DD');
      const todayStr = dayjs(today).format('YYYY-MM-DD');
      newDateRange = [startStr, todayStr];
      console.log(`Year range: ${newDateRange[0]} to ${newDateRange[1]}`);
      break;
    }
    default:
      break;
  }
  
  // 更新本地日期范围
  localDateRange.value = newDateRange;
  
  // 向父组件通知日期范围变化
  emit('update:dateRange', newDateRange);
  
  // 加载数据
  loadRankingData(newDateRange);
};

// 切换交易类型
const changeType = (type) => {
  currentType.value = type;
  transactionType.value = type;
  loadRankingData(localDateRange.value);
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 格式化金额
const formatAmount = (amount) => {
  // 确保amount是数字
  const numAmount = parseFloat(amount);
  if (isNaN(numAmount)) {
    console.error('[TransactionRanking] Invalid amount in formatAmount:', amount);
    return '¥ 0.00';
  }
  return `¥ ${numAmount.toFixed(2)}`;
};

// 表头样式
const headerStyle = () => {
  return {
    backgroundColor: '#f5f7fa',
    color: '#606266',
    fontWeight: 'bold',
  };
};

// 高亮今天的交易
const getRowClassName = ({ row }) => {
  const today = dayjs().format('YYYY-MM-DD');
  const rowDate = formatDate(row.date);
  return rowDate === today ? 'today-row' : '';
};

// 根据分类获取颜色
const getCategoryColor = (category) => {
  const categoryColors = {
    '餐饮美食': '#FF6B6B', // 鲜红色
    '交通出行': '#FFD93D', // 明黄色
    '服饰美容': '#6BCB77', // 翠绿色
    '日用百货': '#4D96FF', // 亮蓝色
    '住房物业': '#9B59B6', // 紫色
    '医疗健康': '#00A896', // 青蓝色 
    '文教娱乐': '#FF9671', // 橙色
    '人情往来': '#FFC75F', // 金黄色
    '工资薪酬': '#43AA8B', // 青绿色
    '投资理财': '#277DA1', // 深蓝色
    '奖金': '#5D8CAE', // 钴蓝色
    '退款': '#63B7AF', // 薄荷绿
    '兼职收入': '#68C3D4', // 天蓝色
    '租金收入': '#826AED', // 紫罗兰
    '礼金收入': '#C05780', // 玫瑰红
    '中奖收入': '#F08A5D', // 珊瑚橙
    '意外所得': '#B83B5E', // 酒红色
    '其他收入': '#F94892', // 粉红色
    '其他支出': '#90BE6D', // 嫩绿色
    '未分类': '#98C1D9',   // 灰蓝色
    '食品': '#FF9E80'      // 橙红色 
  };

  return categoryColors[category] || '#98C1D9';  
};

// 切换排序方式
const changeSortBy = (sort) => {
  console.log('[TransactionRanking] Changing sort to:', sort);
  sortBy.value = sort;
  loadRankingData(localDateRange.value, transactionType.value, sortBy.value);
};
</script>

<style scoped>
.transaction-ranking {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #E3F2ED;
  padding: 15px;
  border-radius: 18px;
  gap: 15px;
}

.filter-container {
  background-color: #fff;
  padding: 16px 20px;
  border-radius: 16px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px solid #A7E0C7;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

/* 排序选择器样式 */
.sort-container {
  background-color: #fff;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(61, 110, 89, 0.08);
  display: flex;
  align-items: center;
  gap: 16px;
}

.sort-label {
  color: #3D6E59;
  font-weight: 500;
}

.sort-options {
  display: flex;
  gap: 8px;
}

.filter-btns .el-button,
.type-tabs .el-button,
.sort-options .el-button {
  margin-right: 8px;
}

.filter-btns .el-button.active,
.type-tabs .el-button.active,
.sort-options .el-button.active {
  background-color: #3D6E59;
  border-color: #3D6E59;
  color: white;
}

.category-tag {
  color: #fff !important;
  border: none;
}

/* 美化表单元素 */
:deep(.el-radio-group) .el-radio-button__inner {
  border-radius: 14px;
  border: 1px solid #8CDAB6;
  background-color: #F0FBF7;
  color: #3D6E59;
  font-size: 14px;
  transition: all 0.3s ease;
}

:deep(.el-radio-group) .el-radio-button.is-active .el-radio-button__inner {
  background-color: #5DAF8E;
  border-color: #5DAF8E;
  color: white;
  box-shadow: 0 0 8px rgba(93, 175, 142, 0.5);
}

:deep(.el-select) .el-input__wrapper {
  border-radius: 14px;
  border: 1px solid #A7E0C7;
  background-color: #F0FBF7;
  box-shadow: none !important;
}

:deep(.el-select):hover .el-input__wrapper {
  border-color: #5DAF8E;
}

:deep(.el-select-dropdown__item.selected) {
  color: #3D6E59;
  font-weight: bold;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: #E3F2ED;
}

.ranking-list {
  flex-grow: 1;
  overflow-y: auto;
  background-color: #fff;
  border-radius: 16px;
  padding: 15px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px solid #A7E0C7;
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

/* 自定义标签样式 */
:deep(.el-tag) {
  border-radius: 12px;
  padding: 0 10px;
  border: none;
  font-weight: 500;
}

:deep(.el-tag--danger) {
  background-color: #FFF0F0;
  color: #FF6B6B;
}

:deep(.el-tag--warning) {
  background-color: #FFFAEB;
  color: #FFD93D;
}

:deep(.el-tag--success) {
  background-color: #F0F9EB;
  color: #6BCB77;
}

:deep(.el-tag--info) {
  background-color: #F0F7FF;
  color: #4D96FF;
}

:deep(.el-tag--purple) {
  background-color: #F8F0FC;
  color: #9B59B6;
}

:deep(.el-tag--orange) {
  background-color: #FFF7F0;
  color: #FF9671;
}

:deep(.el-tag--gold) {
  background-color: #FFFBEB;
  color: #FFC75F;
}

:deep(.el-tag--teal) {
  background-color: #F0F9F4;
  color: #43AA8B;
}

:deep(.el-tag--primary) {
  background-color: #EFF8FF;
  color: #277DA1;
}

:deep(.el-tag--pink) {
  background-color: #FFF0F7;
  color: #F94892;
}

:deep(.el-tag--lime) {
  background-color: #F6FFF0;
  color: #90BE6D;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: center;
}

:deep(.el-pagination) {
  --el-pagination-button-color: #3D6E59;
  --el-pagination-hover-color: #5DAF8E;
}

:deep(.el-pagination .btn-prev),
:deep(.el-pagination .btn-next),
:deep(.el-pagination .el-pager li) {
  background-color: #E8F6F0;
  border-radius: 50%;
  margin: 0 3px;
}

:deep(.el-pagination .el-pager li.is-active) {
  background-color: #5DAF8E;
  color: white;
}

:deep(.el-pagination .el-pager li:hover) {
  color: #5DAF8E;
}

.income-amount {
  color: #3CB371;
  font-weight: bold;
}

.expense-amount {
  color: #3D6E59;
  font-weight: bold;
}

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

/* 高亮今天的交易记录，但不加粗 */
:deep(.today-row) {
  --el-table-tr-bg-color: #e6f7ff;
}
</style> 