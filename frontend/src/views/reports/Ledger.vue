<template>
  <div class="ledger">
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
      <div class="filter-header">
        <h3>每日报表</h3>
        <div class="filter-tabs">
          <el-radio-group v-model="transactionType" size="small">
            <el-radio-button label="balance">结余</el-radio-button>
            <el-radio-button label="income">收入</el-radio-button>
            <el-radio-button label="expense">支出</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div class="filter-options">
        <div class="filter-item">
          <span class="filter-label">分类:</span>
          <el-select v-model="category" placeholder="选择分类" clearable size="small" class="category-select">
            <el-option-group label="支出分类">
              <el-option v-for="item in expenseCategories" :key="item" :label="item" :value="item" />
            </el-option-group>
            <el-option-group label="收入分类">
              <el-option v-for="item in incomeCategories" :key="item" :label="item" :value="item" />
            </el-option-group>
          </el-select>
        </div>
      </div>
    </div>
    
    <!-- 分类饼图部分 -->
    <div v-if="transactionType !== 'balance'" class="mint-pie-chart-container" v-loading="categoryChartLoading">
      <div class="mint-pie-chart-header">
        <h3>{{ transactionType === 'income' ? '收入' : '支出' }}分类占比</h3>
        <div class="chart-note">✨ {{ transactionType === 'income' ? '收入来源' : '花钱去向' }}一目了然 ✨</div>
      </div>
      <div class="mint-pie-chart-content">
        <div v-if="categoryChartLoading" class="chart-placeholder">
          <el-empty description="正在准备饼图..." />
        </div>
        <div v-else-if="!categoryData || categoryData.length === 0" class="chart-placeholder">
          <el-empty description="暂时没有数据呢 (˘･_･˘)" />
        </div>
        <div v-else id="categoryPieChart" class="mint-chart"></div>
      </div>
    </div>
      
      <div class="ledger-container" v-loading="chartLoading">
        <!-- 结余部分 -->
        <div v-if="transactionType === 'balance'" class="ledger-section balance-section">
          <h3 class="section-title balance-title">每日结余</h3>
      <el-table
            :data="balanceData"
        stripe
        style="width: 100%"
        :default-sort="{ prop: 'date', order: 'descending' }"
            class="balance-table"
      >
            <el-table-column prop="date" label="日期" sortable width="200" />
            <el-table-column prop="amount" label="结余金额" width="160" align="right">
          <template #default="scope">
                <span :class="scope.row.type === 'income' ? 'income-amount' : 'expense-amount'">
              {{ scope.row.type === 'income' ? '+' : '-' }} {{ scope.row.amount }}
            </span>
          </template>
        </el-table-column>
            <el-table-column prop="description" label="描述" min-width="240" />
          </el-table>
        </div>
        
        <!-- 收入部分 -->
        <div v-if="transactionType === 'income'" class="ledger-section income-section">
          <h3 class="section-title income-title">每日收入</h3>
          <el-table
            :data="incomeData"
            stripe
            style="width: 100%"
            :default-sort="{ prop: 'date', order: 'descending' }"
            class="income-table"
          >
            <el-table-column prop="date" label="日期" sortable width="200" />
            <el-table-column prop="amount" label="收入金额" width="160" align="right">
          <template #default="scope">
                <span class="income-amount">
                  + {{ scope.row.amount }}
                </span>
          </template>
        </el-table-column>
            <el-table-column prop="description" label="描述" min-width="240" />
      </el-table>
        </div>
        
        <!-- 支出部分 -->
        <div v-if="transactionType === 'expense'" class="ledger-section expense-section">
          <h3 class="section-title expense-title">每日支出</h3>
          <el-table
            :data="expenseData"
            stripe
            style="width: 100%"
            :default-sort="{ prop: 'date', order: 'descending' }"
            class="expense-table"
          >
            <el-table-column prop="date" label="日期" sortable width="200" />
            <el-table-column prop="amount" label="支出金额" width="160" align="right">
              <template #default="scope">
                <span class="expense-amount">
                  - {{ scope.row.amount }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="240" />
          </el-table>
        </div>
    </div>
    
    <div class="pagination">
      <el-pagination
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pageSize"
        :current-page="currentPage"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 交易编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'edit' ? '编辑交易记录' : '删除交易记录'"
      width="500px"
    >
      <template v-if="dialogType === 'edit'">
        <el-form :model="editForm" label-width="80px">
          <el-form-item label="交易类型">
            <el-select v-model="editForm.type" style="width: 100%">
              <el-option label="收入" value="income" />
              <el-option label="支出" value="expense" />
            </el-select>
          </el-form-item>
          <el-form-item label="日期">
            <el-date-picker
              v-model="editForm.date"
              type="date"
              format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="金额">
            <el-input-number v-model="editForm.amount" :min="0" :precision="2" style="width: 100%" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="editForm.description" />
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="editForm.category" style="width: 100%">
              <el-option-group label="支出分类" v-if="editForm.type === 'expense'">
                <el-option v-for="item in expenseCategories" :key="item" :label="item" :value="item" />
              </el-option-group>
              <el-option-group label="收入分类" v-if="editForm.type === 'income'">
                <el-option v-for="item in incomeCategories" :key="item" :label="item" :value="item" />
              </el-option-group>
            </el-select>
          </el-form-item>
        </el-form>
      </template>
      <template v-else>
        <p>确定要删除这条交易记录吗？此操作不可撤销。</p>
        <div class="transaction-info">
          <div><strong>日期:</strong> {{ editForm.date }}</div>
          <div><strong>描述:</strong> {{ editForm.description }}</div>
          <div><strong>分类:</strong> {{ editForm.category }}</div>
          <div>
            <strong>金额:</strong> 
              <span :class="{
                'income-amount': editForm.type === 'income' && !editForm.description.includes('结余'), 
                'expense-amount': editForm.type === 'expense' && !editForm.description.includes('结余'),
                'balance-amount': editForm.description.includes('结余')
              }">
              {{ editForm.type === 'income' ? '+' : '-' }} {{ editForm.amount }}
            </span>
          </div>
        </div>
      </template>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" v-if="dialogType === 'edit'" @click="saveTransaction">保存</el-button>
          <el-button type="danger" v-else @click="confirmDelete">确认删除</el-button>
        </span>
      </template>
    </el-dialog>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox, ElSkeleton, ElAlert, ElButton } from 'element-plus';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useUserStore } from '../../store/user';
import * as echarts from 'echarts';

const router = useRouter();
const userStore = useUserStore();

// 创建axios实例
const apiInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // 确保请求不会缓存，避免刷新问题
  params: {
    '_': Date.now() // 添加时间戳参数，防止浏览器缓存
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
  
  // 对于GET请求，确保添加时间戳避免缓存问题
  if (config.method === 'get') {
    config.params = config.params || {};
    config.params['_t'] = new Date().getTime();
  }
  
  return config;
}, error => {
  console.error('[API Interceptor] Request error:', error);
  return Promise.reject(error);
});

// 添加响应拦截器
apiInstance.interceptors.response.use(
  response => {
    // 正常响应
    return response;
  },
  error => {
    // 错误处理
    if (error.response) {
      // 处理服务端返回的错误
      switch (error.response.status) {
        case 405: // Method Not Allowed
          console.error('[API Error] Method Not Allowed detected');
          router.push({ name: 'dashboard' }); // 跳转到仪表盘页面
          break;
        case 401: // Unauthorized
          console.error('[API Error] Unauthorized detected');
          userStore.logout(); // 注销用户
          router.push({ name: 'login' }); // 跳转到登录页面
          break;
      }
    }
    return Promise.reject(error);
  }
);

const props = defineProps({
  dateRange: {
    type: Array,
    required: true
  }
});

// 筛选条件
const transactionType = ref('balance');
const category = ref('');

// 分页
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 对话框
const dialogVisible = ref(false);
const dialogType = ref('edit');
const editForm = reactive({
  id: null,
  type: 'expense',
  date: '',
  amount: 0,
  description: '',
  category: ''
});

// 状态管理
const tableData = ref([]);
const balanceData = ref([]);
const incomeData = ref([]);
const expenseData = ref([]);
const loading = ref(false);
const chartLoading = ref(false);
const categoryChartLoading = ref(false);
const categoryData = ref([]);
const error = ref(false);
const errorMessage = ref('');
const authLoading = ref(true);

// 图表实例
let categoryChart = null;

// 表格行类名
const rowClassName = ({ row }) => {
  if (row.isBalance) return 'balance-row';
  if (row.isIncome) return 'income-row';
  if (row.isExpense) return 'expense-row';
  return '';
};

// 分类列表
const expenseCategories = [
  '餐饮美食', '交通出行', '服饰美容', '日用百货',
  '住房物业', '医疗健康', '文教娱乐', '人情往来', '其他支出'
];
const incomeCategories = [
  '工资薪酬', '投资理财', '其他收入'
];

// 获取类别颜色
const getCategoryColor = (category) => {
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
  return categoryColors[category] || '#A7E0C7';
}

// 去登录页
const goToLogin = () => {
  router.push({ name: 'login', query: { redirect: window.location.pathname + window.location.search } });
};

// 重试加载数据
const retryLoading = () => {
  initializeAuthAndLoad();
};

// 监听筛选条件变化
watch(
  [() => props.dateRange, transactionType, category],
  ([newDateRange, newType, newCategory], [oldDateRange, oldType, oldCategory]) => {
    console.log('[Ledger] Filter changed:', { 
      dateRange: { new: newDateRange, old: oldDateRange },
      type: { new: newType, old: oldType },
      category: { new: newCategory, old: oldCategory }
    });
    
    // 防止初始化时重复加载
    if (authLoading.value) {
      console.log('[Ledger] Skipping watcher during auth loading');
      return;
    }
    
    if (newDateRange && newDateRange.length === 2 && 
        (JSON.stringify(newDateRange) !== JSON.stringify(oldDateRange) || 
         newType !== oldType || 
         newCategory !== oldCategory)) {
      console.log('[Ledger] Loading data due to filter change');
      currentPage.value = 1;
      fetchTransactions();
      
      // 当类型变更为收入或支出时，加载类别图表
      if (newType !== oldType && newType !== 'balance') {
        fetchCategoryData();
      }
    }
  }
);

// 获取分类数据并渲染饼图
const fetchCategoryData = async () => {
  if (transactionType.value === 'balance') return;
  
  console.log('[Ledger] fetchCategoryData - Start. Type:', transactionType.value);
  categoryChartLoading.value = true;
  
  try {
    // 检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[Ledger] fetchCategoryData: No token found. Aborting.');
      return;
    }
    
    if (!props.dateRange || props.dateRange.length !== 2) {
      console.warn('[Ledger] fetchCategoryData: No date range provided');
      return;
    }
    
    const response = await apiInstance.get('/reports/category-ranking', {
      params: {
        transaction_type: transactionType.value,
        start_date: props.dateRange[0],
        end_date: props.dateRange[1]
      }
    });
    
    console.log('[Ledger] fetchCategoryData - API response received:', response.data);
    
    // 处理API返回的数据
    const data = response.data;
    categoryData.value = data.map((item) => ({
      category: item.category,
      amount: item.total_amount,
      percentage: item.percentage
    }));
    
    // 渲染饼图
    renderCategoryChart();
  } catch (err) {
    console.error('[Ledger] fetchCategoryData - Error during API call:', err);
    categoryData.value = [];
  } finally {
    categoryChartLoading.value = false;
    console.log('[Ledger] fetchCategoryData - Finished.');
  }
};

// 渲染分类饼图
const renderCategoryChart = () => {
  if (!categoryData.value || categoryData.value.length === 0) return;
  
  // 确保DOM已渲染
  setTimeout(() => {
    const chartDom = document.getElementById('categoryPieChart');
    if (!chartDom) {
      console.warn('[Ledger] renderCategoryChart - Chart DOM element not found');
      return;
    }
    
    // 如果图表已存在，先销毁
    if (categoryChart) {
      categoryChart.dispose();
    }
    
    // 初始化图表
    categoryChart = echarts.init(chartDom);
    
    const pieData = categoryData.value.map(item => ({
      name: item.category,
      value: item.amount
    }));
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}: {c} ({d}%)',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderColor: transactionType.value === 'income' ? '#3CB371' : '#5DAF8E',
        borderWidth: 2,
        padding: [8, 12],
        textStyle: {
          color: '#3D6E59'
        }
      },
      legend: {
        type: 'scroll',
        bottom: '0%',
        icon: 'circle',
        itemWidth: 12,
        itemHeight: 12,
        itemGap: 10,
        textStyle: {
          fontSize: 12,
          color: '#3D6E59'
        },
        pageIconColor: transactionType.value === 'income' ? '#3CB371' : '#5DAF8E',
        pageTextStyle: {
          color: '#3D6E59'
        }
      },
      series: [
        {
          name: transactionType.value === 'income' ? '收入' : '支出',
          type: 'pie',
          radius: '65%',
          center: ['50%', '45%'],
          data: pieData,
          roseType: 'radius',
          label: {
            formatter: '{b}: {d}%',
            fontSize: 12,
            fontWeight: 'normal',
            color: '#3D6E59'
          },
          labelLine: {
            length: 10,
            length2: 8,
            smooth: true
          },
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2,
            color: function(params) {
              return getCategoryColor(params.name);
            },
            shadowBlur: 5,
            shadowColor: 'rgba(0, 0, 0, 0.1)'
          },
          animationType: 'scale',
          animationEasing: 'elasticOut'
        }
      ]
    };
    
    categoryChart.setOption(option);
    console.log('[Ledger] renderCategoryChart - Chart rendered successfully');
  }, 0);
};

// 获取交易列表
const fetchTransactions = async () => {
  console.log('[Ledger] fetchTransactions - Start. DateRange:', props.dateRange, 'Type:', transactionType.value, 'Category:', category.value);
  chartLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  
  try {
    // 检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[Ledger] fetchTransactions: No token found. Aborting.');
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
      console.log('[Ledger] fetchTransactions: Token exists but user not logged in. Attempting to restore session...');
      try {
        await userStore.checkAuth();
        if (!userStore.isLoggedIn) {
          console.warn('[Ledger] fetchTransactions: Failed to restore session.');
          error.value = true;
          errorMessage.value = '您的登录已失效，请重新登录。';
          return;
        }
      } catch (err) {
        console.error('[Ledger] fetchTransactions: Error restoring session:', err);
        error.value = true;
        errorMessage.value = '恢复会话失败，请重新登录。';
        return;
      }
    }
    
    // 构建查询参数
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    };
    
    // 添加日期范围参数
    if (props.dateRange && props.dateRange.length === 2) {
      params.start_date = props.dateRange[0];
      params.end_date = props.dateRange[1];
      console.log(`[Ledger] Using date range: ${params.start_date} to ${params.end_date}`);
      
      // 验证日期范围是否合理
      const startDate = new Date(params.start_date);
      const endDate = new Date(params.end_date);
      const daysDiff = Math.floor((endDate - startDate) / (1000 * 60 * 60 * 24));
      console.log(`[Ledger] Date range spans ${daysDiff + 1} days`);
      
      // 如果日期范围过小，尝试扩展范围以确保获取足够数据
      if (daysDiff < 1) {
        const adjustedEnd = new Date(endDate);
        adjustedEnd.setDate(adjustedEnd.getDate() + 1);
        params.end_date = adjustedEnd.toISOString().split('T')[0];
        console.log(`[Ledger] Adjusted date range: ${params.start_date} to ${params.end_date}`);
      }
    } else {
      // 如果没有日期范围，使用当前月份
      const today = new Date();
      const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
      const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      
      params.start_date = firstDay.toISOString().split('T')[0];
      params.end_date = lastDay.toISOString().split('T')[0];
      console.log(`[Ledger] No date range provided, using current month: ${params.start_date} to ${params.end_date}`);
    }
    
    // 添加筛选条件
    if (transactionType.value !== 'balance') {
      params.transaction_type = transactionType.value;
    }
    
    if (category.value) {
      params.category = category.value;
    }
    
    console.log('[Ledger] fetchTransactions - Making API request with params:', params);
    
    // 确保API请求是GET方法，并处理可能的错误
    try {
      const response = await apiInstance.get('/reports/ledger', { params });
      console.log('[Ledger] fetchTransactions - API response received:', response.data);
      
      // 检查返回的数据是否包含多天记录
      if (response.data.daily_records) {
        const dates = response.data.daily_records.map(record => record.date);
        const uniqueDates = [...new Set(dates)];
        console.log(`[Ledger] API returned data for ${uniqueDates.length} unique dates:`, uniqueDates);
      }
      
      // 处理ledger数据，这需要根据实际接口返回格式进行调整
      const data = response.data;
      console.log('[Ledger] fetchTransactions - Raw API response:', data);
      
      // 处理API返回的数据格式
      processApiResponse(data);
      
    } catch (apiErr) {
      console.error('[Ledger] API request error:', apiErr);
      
      // 判断错误是否为Method Not Allowed
      if (apiErr.response && apiErr.response.status === 405) {
        console.warn('[Ledger] Method Not Allowed error detected, redirecting to dashboard');
        // 重定向到仪表盘页面（或其他合适的页面）
        router.push({ name: 'dashboard' });
        return;
      }
      
      throw apiErr; // 重新抛出错误，让外部catch处理
    }
  } catch (err) {
    console.error('[Ledger] fetchTransactions - Error during API call:', err);
    error.value = true;
    
    if (err.response && err.response.status === 401) {
      console.warn('[Ledger] fetchTransactions - Received 401, logging out and redirecting.');
      errorMessage.value = '登录状态已失效，请重新登录。';
      userStore.logout();
    } else {
      errorMessage.value = err.response 
        ? `错误 ${err.response.status}: ${err.response.data?.detail || err.response.statusText || '无法连接到服务器'}` 
        : `网络请求错误: ${err.message || '未知网络错误'}`;
      ElMessage.error(errorMessage.value || '加载账单数据失败，请稍后再试。');
    }
    
    tableData.value = [];
    total.value = 0;
  } finally {
    chartLoading.value = false;
    console.log('[Ledger] fetchTransactions - Finished. chartLoading:', chartLoading.value, 'error:', error.value);
  }
};

// 处理API响应数据的函数
const processApiResponse = (data) => {
  try {
    // 检查新的按天排序格式（带有daily_records数组）
    if (data && data.daily_records && Array.isArray(data.daily_records)) {
      console.log('[Ledger] Processing daily records format');
      processDailyRecordsFormat(data);
    }
    // 检查是否是新格式（带有transactions数组）
    else if (data && data.transactions && Array.isArray(data.transactions)) {
      console.log('[Ledger] Processing new format data with transactions array');
      processTransactionsArray(data);
    } 
    // 检查是否是旧格式（按年月组织的层级数据）
    else if (data && data.year && data.months) {
      console.log('[Ledger] Processing old format data with year/month structure');
      processHierarchicalData(data);
    }
    // 检查是否是按月组织的数据
    else if (data && data.month && data.days) {
      console.log('[Ledger] Processing month/day structure data');
      processMonthDayData(data);
    }
    // 检查是否是按日组织的数据
    else if (data && data.day && data.transactions) {
      console.log('[Ledger] Processing day structure data with transactions');
      processTransactionsFromDay(data);
    }
    // 检查空结果但API成功返回的情况
    else if (data && Object.keys(data).length === 0) {
      console.log('[Ledger] API returned empty data object');
      tableData.value = [];
      total.value = 0;
      
      // 如果是搜索导致的空结果，显示提示
      if (category.value) {
        ElMessage({
          message: `没有找到包含 "${category.value}" 的账单记录`,
          type: 'info',
          duration: 3000
        });
      }
    }
    else {
      console.warn('[Ledger] Unexpected data format:', data);
      tableData.value = [];
      total.value = 0;
      error.value = true;
      errorMessage.value = '无法解析账单数据，请联系管理员。';
    }
  } catch (err) {
    console.error('[Ledger] Error processing data:', err);
    tableData.value = [];
    total.value = 0;
    error.value = true;
    errorMessage.value = `处理账单数据时出错: ${err.message || '未知错误'}`;
  }
};

// 处理带有transactions数组的新格式数据
const processTransactionsArray = (data) => {
  console.log('[Ledger] Processing transactions array:', data.transactions.length, 'items');
  tableData.value = data.transactions.map(tx => {
    // 确保日期格式正确
    let formattedDate = tx.date || tx.transaction_date;
    
    // 处理各种可能的日期格式
    if (formattedDate instanceof Date) {
      formattedDate = formattedDate.toISOString().split('T')[0];
    } else if (typeof formattedDate === 'string') {
      // 如果是ISO格式字符串，提取日期部分
      if (formattedDate.includes('T')) {
        formattedDate = formattedDate.split('T')[0];
      }
      // 确保格式为YYYY-MM-DD
      if (!formattedDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
        console.warn('[Ledger] Invalid date format:', formattedDate);
        formattedDate = '未知日期';
      }
    } else {
      console.warn('[Ledger] Missing or invalid date for transaction:', tx.id);
      formattedDate = '未知日期';
    }
    
    // 处理金额格式
    let amount = 0;
    try {
      amount = Number(tx.amount);
      if (isNaN(amount)) {
        console.warn('[Ledger] Invalid amount format:', tx.amount);
        amount = 0;
      }
    } catch (err) {
      console.error('[Ledger] Error parsing amount:', err);
      amount = 0;
    }
    
    return {
      id: tx.id,
      date: formattedDate,
      type: tx.type || tx.transaction_type || 'expense',
      description: tx.description || '无描述',
      category: tx.category || '未分类',
      amount: amount.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
      isBalance: false,
      isIncome: false,
      isExpense: false
    };
  });
  
  // 使用API返回的总数
  total.value = data.total_count || data.transactions.length;
  console.log('[Ledger] Successfully processed data. Total records:', total.value);
};

// 处理按年月组织的层级数据
const processHierarchicalData = (data) => {
  console.log('[Ledger] Processing hierarchical data with', data.months?.length || 0, 'months');
  
  // 创建虚拟交易记录
  const transactions = [];
  
  // 处理月份数据
  if (data.months && Array.isArray(data.months)) {
    data.months.forEach(month => {
      // 为每个月创建一个收入和支出记录
      if (month.total_income > 0) {
        transactions.push({
          id: `income-${month.month}`,
          date: `${data.year}-${String(month.month).padStart(2, '0')}-01`,
          type: 'income',
          description: `${month.month}月收入总计`,
          category: '月度汇总',
          amount: month.total_income.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
          isBalance: false,
          isIncome: true,
          isExpense: false
        });
      }
      
      if (month.total_expense > 0) {
        transactions.push({
          id: `expense-${month.month}`,
          date: `${data.year}-${String(month.month).padStart(2, '0')}-01`,
          type: 'expense',
          description: `${month.month}月支出总计`,
          category: '月度汇总',
          amount: month.total_expense.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
          isBalance: false,
          isIncome: false,
          isExpense: true
        });
      }
    });
  }
  
  tableData.value = transactions;
  total.value = transactions.length;
  
  // 显示提示信息
  ElMessage({
    message: '当前显示的是月度汇总数据，无法查看详细交易记录',
    type: 'info',
    duration: 5000
  });
  
  console.log('[Ledger] Created', transactions.length, 'virtual transactions from hierarchical data');
};

// 处理按月/日组织的数据
const processMonthDayData = (data) => {
  console.log('[Ledger] Processing month/day data with', data.days?.length || 0, 'days');
  
  // 创建虚拟交易记录
  const transactions = [];
  
  // 处理日数据
  if (data.days && Array.isArray(data.days)) {
    data.days.forEach(day => {
      // 为每天创建一个收入和支出记录
      if (day.total_income > 0) {
        transactions.push({
          id: `income-${day.day}`,
          date: `${data.year}-${String(data.month).padStart(2, '0')}-${String(day.day).padStart(2, '0')}`,
          type: 'income',
          description: `${day.day}日收入总计`,
          category: '日度汇总',
          amount: day.total_income.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
          isBalance: false,
          isIncome: true,
          isExpense: false
        });
      }
      
      if (day.total_expense > 0) {
        transactions.push({
          id: `expense-${day.day}`,
          date: `${data.year}-${String(data.month).padStart(2, '0')}-${String(day.day).padStart(2, '0')}`,
          type: 'expense',
          description: `${day.day}日支出总计`,
          category: '日度汇总',
          amount: day.total_expense.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
          isBalance: false,
          isIncome: false,
          isExpense: true
        });
      }
    });
  }
  
  tableData.value = transactions;
  total.value = transactions.length;
  
  // 显示提示信息
  ElMessage({
    message: '当前显示的是日度汇总数据，无法查看详细交易记录',
    type: 'info',
    duration: 5000
  });
  
  console.log('[Ledger] Created', transactions.length, 'virtual transactions from month/day data');
};

// 处理日级别的交易数据
const processTransactionsFromDay = (data) => {
  console.log('[Ledger] Processing day level transactions:', data.transactions?.length || 0, 'items');
  
  if (data.transactions && Array.isArray(data.transactions)) {
    tableData.value = data.transactions.map(tx => {
      return {
        id: tx.id,
        date: `${data.year}-${String(data.month).padStart(2, '0')}-${String(data.day).padStart(2, '0')}`,
        type: tx.type,
        description: tx.description || '无描述',
        category: tx.category || '未分类',
        amount: Number(tx.amount).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
        isBalance: false,
        isIncome: false,
        isExpense: false
      };
    });
    
    total.value = data.transactions.length;
    console.log('[Ledger] Processed', total.value, 'transactions from day data');
  } else {
    tableData.value = [];
    total.value = 0;
    console.warn('[Ledger] No transactions in day data');
  }
};

// 处理按天排序的账单数据
const processDailyRecordsFormat = (data) => {
  console.log('[Ledger] Processing daily records format with', data.daily_records?.length || 0, 'days');
  console.log('[Ledger] Raw daily_records data:', data.daily_records);
  
  const allTransactions = [];
  const balanceRecords = [];
  const incomeRecords = [];
  const expenseRecords = [];

  // 处理每日记录
  if (data.daily_records && Array.isArray(data.daily_records)) {
    // 检查数组是否为空
    if (data.daily_records.length === 0) {
      console.log('[Ledger] No daily records found, possibly due to search filter');
      // 如果是搜索导致的空结果，显示提示
      if (category.value) {
        ElMessage({
          message: `没有找到包含 "${category.value}" 的账单记录`,
          type: 'info',
          duration: 3000
        });
      }
    } else {
      // 处理有数据的情况
      data.daily_records.forEach(record => {
        // 输出每条记录的日期，方便调试
        console.log(`[Ledger] Processing record for date: ${record.date}`);
        
        // 日期格式化
        const formattedDate = record.date;
        // 日期对象，用于格式化显示
        const dateObj = new Date(record.date);
        const dayOfWeek = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][dateObj.getDay()];
        const dayStr = `${formattedDate} ${dayOfWeek}`;
        
        // 提取日期部分用于分组和排序
        const dateKey = formattedDate;

        // 创建结余记录并添加到结余数组
        const balanceRecord = {
          id: `balance-${record.date}`,
          date: dayStr,
          rawDate: dateObj, // 保存原始日期对象用于排序
          type: record.balance >= 0 ? 'income' : 'expense',
          description: `当日结余`,
          category: '日度汇总',
          amount: Math.abs(record.balance).toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
          isBalance: true,
          dateKey: dateKey
        };
        balanceRecords.push(balanceRecord);
        allTransactions.push(balanceRecord);

        // 创建收入记录并添加到收入数组
        if (record.total_income > 0) {
          const incomeRecord = {
            id: `income-${record.date}`,
            date: dayStr,
            rawDate: dateObj, // 保存原始日期对象用于排序
            type: 'income',
            description: `当日收入`,
            category: '日度汇总',
            amount: record.total_income.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
            isIncome: true,
            dateKey: dateKey
          };
          incomeRecords.push(incomeRecord);
          allTransactions.push(incomeRecord);
        }

        // 创建支出记录并添加到支出数组
        if (record.total_expense > 0) {
          const expenseRecord = {
            id: `expense-${record.date}`,
            date: dayStr,
            rawDate: dateObj, // 保存原始日期对象用于排序
            type: 'expense',
            description: `当日支出`,
            category: '日度汇总',
            amount: record.total_expense.toLocaleString('zh-CN', {minimumFractionDigits: 2, maximumFractionDigits: 2}),
            isExpense: true,
            dateKey: dateKey
          };
          expenseRecords.push(expenseRecord);
          allTransactions.push(expenseRecord);
        }
      });
    }
  } else {
    // 数据格式错误
    console.warn('[Ledger] Invalid daily_records format in API response');
    if (!error.value) {
      ElMessage.warning('服务器返回的数据格式有误');
    }
  }

  // 按日期降序排序每个数组
  const sortByDateDesc = (a, b) => {
    // 使用原始日期对象比较而不是字符串，避免排序问题
    return b.rawDate - a.rawDate;
  };

  // 输出未排序状态的数据
  console.log('[Ledger] Before sorting - balanceRecords:', balanceRecords.map(r => r.dateKey));
  console.log('[Ledger] Before sorting - incomeRecords:', incomeRecords.map(r => r.dateKey));
  console.log('[Ledger] Before sorting - expenseRecords:', expenseRecords.map(r => r.dateKey));

  balanceRecords.sort(sortByDateDesc);
  incomeRecords.sort(sortByDateDesc);
  expenseRecords.sort(sortByDateDesc);

  // 输出排序后的数据
  console.log('[Ledger] After sorting - balanceRecords:', balanceRecords.map(r => r.dateKey));
  console.log('[Ledger] After sorting - incomeRecords:', incomeRecords.map(r => r.dateKey));
  console.log('[Ledger] After sorting - expenseRecords:', expenseRecords.map(r => r.dateKey));

  // 更新视图数据
  balanceData.value = balanceRecords;
  incomeData.value = incomeRecords;
  expenseData.value = expenseRecords;
  tableData.value = allTransactions;
  
  // 设置总记录数，支持分页
  total.value = data.total_count || allTransactions.length;
  
  console.log('[Ledger] Created', allTransactions.length, 'transactions from daily records data', {
    balance: balanceRecords.length,
    income: incomeRecords.length,
    expense: expenseRecords.length
  });
};

// 处理每页条数变化
const handleSizeChange = (size) => {
  console.log('[Ledger] Page size changed to:', size);
  pageSize.value = size;
  fetchTransactions();
};

// 处理页码变化
const handleCurrentChange = (page) => {
  console.log('[Ledger] Page changed to:', page);
  currentPage.value = page;
  fetchTransactions();
};

// 打开编辑对话框
const editTransaction = (row) => {
  // 检查是否是虚拟汇总记录
  if (row.id && (String(row.id).startsWith('income-') || 
                 String(row.id).startsWith('expense-') || 
                 String(row.id).startsWith('balance-'))) {
    // 如果是虚拟汇总记录，显示提示信息
    ElMessage({
      message: '汇总数据无法编辑，请使用交易管理页面编辑具体交易',
      type: 'warning',
      duration: 3000
    });
    return;
  }
  
  dialogType.value = 'edit';
  Object.assign(editForm, {
    id: row.id,
    type: row.type,
    date: row.date,
    amount: parseFloat(row.amount.replace(/[^\d.-]/g, '')),
    description: row.description,
    category: row.category
  });
  dialogVisible.value = true;
};

// 打开删除确认对话框
const deleteTransaction = (row) => {
  // 检查是否是虚拟汇总记录
  if (row.id && (String(row.id).startsWith('income-') || 
                 String(row.id).startsWith('expense-') || 
                 String(row.id).startsWith('balance-'))) {
    // 如果是虚拟汇总记录，显示提示信息
    ElMessage({
      message: '汇总数据无法删除，请使用交易管理页面删除具体交易',
      type: 'warning',
      duration: 3000
    });
    return;
  }
  
  dialogType.value = 'delete';
  Object.assign(editForm, {
    id: row.id,
    type: row.type,
    date: row.date,
    amount: row.amount,
    description: row.description,
    category: row.category
  });
  dialogVisible.value = true;
};

// 保存编辑后的交易
const saveTransaction = async () => {
  try {
    await apiInstance.put(`/transactions/${editForm.id}`, {
      type: editForm.type,
      transaction_date: editForm.date,
      amount: editForm.amount,
      description: editForm.description,
      category: editForm.category
    });
    
    dialogVisible.value = false;
    ElMessage.success('交易记录已更新');
    fetchTransactions();
  } catch (err) {
    console.error('[Ledger] saveTransaction - Error:', err);
    ElMessage.error('更新交易记录失败，请稍后再试');
  }
};

// 确认删除交易
const confirmDelete = async () => {
  try {
    await apiInstance.delete(`/transactions/${editForm.id}`);
    
    dialogVisible.value = false;
    ElMessage.success('交易记录已删除');
    fetchTransactions();
  } catch (err) {
    console.error('[Ledger] confirmDelete - Error:', err);
    ElMessage.error('删除交易记录失败，请稍后再试');
  }
};

// 初始化认证和加载数据
const initializeAuthAndLoad = async () => {
  authLoading.value = true;
  error.value = false;
  errorMessage.value = '';
  console.log('[Ledger] initializeAuthAndLoad - Start. Initial authLoading:', authLoading.value);
  
  try {
    // 先检查token是否存在
    const sessionToken = sessionStorage.getItem('token');
    const localToken = localStorage.getItem('token');
    const hasToken = !!userStore.token || !!localToken || !!sessionToken;
    
    if (!hasToken) {
      console.warn('[Ledger] initializeAuthAndLoad - No token found. User needs to login.');
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
      console.log('[Ledger] initializeAuthAndLoad - Attempting to verify authentication');
      await userStore.checkAuth();
      console.log('[Ledger] initializeAuthAndLoad - Auth check completed. User logged in:', userStore.isLoggedIn);

      if (!userStore.isLoggedIn) {
        console.warn('[Ledger] User not authenticated after checkAuth');
        errorMessage.value = '认证失败，请重新登录。';
        error.value = true;
        return;
      }
    } catch (authError) {
      console.error('[Ledger] Authentication error:', authError);
      errorMessage.value = '认证失败，请重新登录。';
      error.value = true;
      return;
    }

    console.log('[Ledger] Loading data after successful authentication check');
    
    // 加载账本数据
      if (props.dateRange && props.dateRange.length === 2) {
        await fetchTransactions();
        if (transactionType.value !== 'balance') {
          await fetchCategoryData();
        }
      } else {
        console.warn('[Ledger] initializeAuthAndLoad - Date range not ready for initial load.');
      }
  } catch (error) {
    console.error('[Ledger] Error in initializeAuthAndLoad:', error);
    errorMessage.value = `加载失败: ${error.message || '未知错误'}`;
    error.value = true;
  } finally {
    console.log('[Ledger] initializeAuthAndLoad completed');
    authLoading.value = false;
  }
};

// 组件挂载时初始化
onMounted(() => {
  console.log('[Ledger] Component mounted. Initial dateRange:', props.dateRange);
  
  // 捕获可能的初始化错误
  try {
    // 确保有日期范围
    if (!props.dateRange || props.dateRange.length !== 2) {
      console.warn('[Ledger] No date range provided on mount, using default');
      const today = new Date();
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(today.getDate() - 30);
      
      // 格式化为YYYY-MM-DD
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };
      
      // 不直接修改props，而是通过父组件的事件处理
      console.log('[Ledger] Using default date range:', formatDate(thirtyDaysAgo), 'to', formatDate(today));
    }
    
    // 检查当前URL是否合法
    const currentPath = window.location.pathname;
    if (currentPath.includes('/reports/ledger') || currentPath.includes('/reports')) {
      console.log('[Ledger] Valid path detected:', currentPath);
      initializeAuthAndLoad();
    } else {
      console.warn('[Ledger] Invalid path detected, redirecting to dashboard');
      router.push({ name: 'dashboard' });
    }
  } catch (err) {
    console.error('[Ledger] Error during component initialization:', err);
    // 出错时显示错误信息并提供重新加载选项
    error.value = true;
    errorMessage.value = '页面加载时发生错误，请刷新重试';
    ElMessage.error('页面初始化失败，即将返回仪表盘');
    
    // 延迟跳转，让用户看到错误信息
    setTimeout(() => {
      router.push({ name: 'dashboard' });
    }, 2000);
  }
});

onUnmounted(() => {
  // 销毁图表实例
  if (categoryChart) {
    categoryChart.dispose();
    categoryChart = null;
  }
  
  // 移除事件监听
  window.removeEventListener('resize', () => {
    categoryChart && categoryChart.resize();
  });
});

// 查看日交易明细
const viewDayDetails = (row) => {
  console.log('[Ledger] View day details for:', row);
  
  // 从日期字符串提取年月日
  const dateParts = row.dateKey.split('-');
  if (dateParts.length !== 3) {
    ElMessage.error('日期格式错误，无法查看明细');
    return;
  }
  
  const year = parseInt(dateParts[0]);
  const month = parseInt(dateParts[1]);
  const day = parseInt(dateParts[2]);
  
  // 构建查询参数
  const queryParams = {
    year: year,
    month: month,
    day: day
  };
  
  // 根据当前标签页类型添加额外的筛选条件
  if (transactionType.value === 'income') {
    queryParams.transaction_type = 'INCOME';
  } else if (transactionType.value === 'expense') {
    queryParams.transaction_type = 'EXPENSE';
  }
  
  // 显示加载中的提示
  ElMessage({
    message: '正在加载交易明细...',
    type: 'info',
    duration: 1000
  });
  
  // 跳转到明细排行页面，带上日期参数
  router.push({
    name: 'ranking',
    query: queryParams
  });
};
</script>

<style scoped>
.ledger {
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
  margin-bottom: 20px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  border-bottom: 1px dashed #A7E0C7;
  padding-bottom: 10px;
}

.filter-header h3 {
  margin: 0;
  color: #3D6E59;
  font-size: 18px;
  font-weight: 500;
}

.filter-tabs {
  display: flex;
  gap: 10px;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-label {
  color: #3D6E59;
  font-weight: 500;
}

.category-select {
  width: 160px;
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

:deep(.el-select-dropdown__item):hover {
  background-color: #E3F2ED;
}

.ledger-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  min-height: 300px;
}

.ledger-section {
  margin-bottom: 20px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  background-color: #fff;
  border: 2px solid #A7E0C7;
  width: 100%;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-title {
  padding: 14px 16px;
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.balance-title {
  background-color: #E0F4FF;
  color: #5DAF8E;
  border-bottom: 2px solid #A7E0C7;
}

.income-title {
  background-color: #E3F2ED;
  color: #3CB371;
  border-bottom: 2px solid #A7E0C7;
}

.expense-title {
  background-color: #E8F6F0;
  color: #3D6E59;
  border-bottom: 2px solid #A7E0C7;
}

.pagination {
  margin-top: 20px;
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

.balance-amount {
  color: #5DAF8E;
  font-weight: bold;
}

/* 文本样式 */
.balance-text {
  font-weight: bold;
  color: #5DAF8E;
}

.income-text {
  color: #3CB371;
}

.expense-text {
  color: #3D6E59;
}

/* 行样式 */
:deep(.balance-row) {
  background-color: rgba(93, 175, 142, 0.1) !important;
}

:deep(.income-row) {
  background-color: rgba(60, 179, 113, 0.05) !important;
}

:deep(.expense-row) {
  background-color: rgba(61, 110, 89, 0.05) !important;
}

/* 当鼠标悬停时的行样式 */
:deep(.balance-row:hover) {
  background-color: rgba(93, 175, 142, 0.2) !important;
}

:deep(.income-row:hover) {
  background-color: rgba(60, 179, 113, 0.1) !important;
}

:deep(.expense-row:hover) {
  background-color: rgba(61, 110, 89, 0.1) !important;
}

/* 美化表格样式 */
:deep(.el-table) {
  border-radius: 12px !important;
  overflow: hidden;
  height: 100%;
  flex: 1;
  width: 100% !important; /* 强制表格占满容器宽度 */
}

:deep(.el-table__inner-wrapper) {
  height: 100%;
}

:deep(.el-table__body-wrapper) {
  height: 100%;
}

:deep(.el-table th) {
  background-color: #E8F6F0 !important;
  color: #3D6E59;
  font-weight: 500;
}

:deep(.el-table td) {
  color: #4E6E61;
  padding: 12px 0; /* 增加行高 */
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #F0FBF7;
}

:deep(.el-table__body tr:hover > td) {
  background-color: #C6F7E2 !important;
}

/* 链接按钮样式 */
:deep(.el-button--text) {
  color: #5DAF8E;
}

:deep(.el-button--text:hover) {
  color: #3D6E59;
}

/* 修复表格宽度问题 */
:deep(.el-table__header),
:deep(.el-table__body),
:deep(.el-table__footer) {
  width: 100% !important;
}

:deep(.el-table__body-wrapper) {
  width: 100% !important;
}

:deep(.el-table .cell) {
  padding-left: 12px !important;
  padding-right: 12px !important;
  line-height: 24px;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0 !important;
}

.transaction-info {
  background-color: #F0FBF7;
  border-radius: 10px;
  padding: 15px;
  margin: 10px 0;
  border: 1px solid #A7E0C7;
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

/* 薄荷绿风格饼图样式 */
.mint-pie-chart-container {
  background-color: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 16px rgba(61, 110, 89, 0.1);
  border: 2px solid #A7E0C7;
  padding: 20px;
  margin-bottom: 20px;
}

.mint-pie-chart-header {
  text-align: center;
  margin-bottom: 15px;
}

.mint-pie-chart-header h3 {
  font-size: 18px;
  color: #3D6E59;
  margin-bottom: 5px;
  font-weight: 500;
}

.chart-note {
  font-size: 13px;
  color: #5DAF8E;
  margin-bottom: 10px;
}

.mint-pie-chart-content {
  height: 280px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.mint-chart {
  width: 100%;
  height: 100%;
}

.chart-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
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