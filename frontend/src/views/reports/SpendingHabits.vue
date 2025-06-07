<template>
  <div class="spending-habits-container">
    <div class="header-section">
      <h2 class="main-title">消费习惯分析</h2>
      <div class="date-range">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="fetchData"
          :default-value="[
            new Date(new Date().setDate(new Date().getDate() - 30)), 
            new Date()
          ]"
        />
      </div>
    </div>

    <div class="top-tabs">
      <div 
        class="top-tab-item" 
        :class="{ active: activeTab === 'habits' }" 
        @click="activeTab = 'habits'"
      >
        <i class="el-icon-data-analysis"></i> 消费习惯分析
      </div>
      <div 
        class="top-tab-item" 
        :class="{ active: activeTab === 'advice' }" 
        @click="activeTab = 'advice'"
      >
        <i class="el-icon-money"></i> 财务改善建议
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>数据加载中，请稍候...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <div class="error-icon">⚠️</div>
      <div>{{ error }}</div>
      <button class="retry-button" @click="fetchData">重试</button>
    </div>

    <div v-else class="analysis-container">
      <template v-if="!hasData">
        <div class="card no-data-card">
          <div class="no-data-icon">📊</div>
          <h3>暂无数据</h3>
          <p>该时间范围内没有消费记录或分析数据。</p>
          <p>请尝试选择其他日期范围或添加一些交易记录。</p>
          <button class="action-button" @click="fetchData">刷新数据</button>
        </div>
      </template>

      <template v-else>
        <!-- 始终显示AI分析区域，不受activeTab影响 -->
        <div v-if="activeTab === 'habits' && aiAnalysis.habits_analysis" class="card analysis-card">
          <h3 class="card-title">消费分析</h3>
          <div class="analysis-text" v-html="formattedAnalysis"></div>
        </div>

        <div v-if="activeTab === 'advice' && aiAnalysis.financial_advice" class="card advice-card">
          <h3 class="card-title">财务建议</h3>
          <div class="analysis-text" v-html="formattedAdvice"></div>
        </div>

        <!-- 只有当有基础统计数据时才显示这部分 -->
        <template v-if="basicStats.totalSpending > 0 || basicStats.totalIncome > 0 || basicStats.transactionCount > 0">
          <div v-if="activeTab === 'habits'" class="card stats-card">
            <h3 class="card-title">基本统计</h3>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">总支出</div>
                <div class="stat-value">¥{{ basicStats.totalSpending.toFixed(2) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">总收入</div>
                <div class="stat-value">¥{{ basicStats.totalIncome.toFixed(2) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">平均每笔支出</div>
                <div class="stat-value">¥{{ basicStats.averageTransaction.toFixed(2) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">交易次数</div>
                <div class="stat-value">{{ basicStats.transactionCount }}</div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'habits' && recentTransactions.length > 0" class="card transactions-card">
            <h3 class="card-title">近期交易记录</h3>
            <table class="transactions-table">
              <thead>
                <tr>
                  <th>日期</th>
                  <th>描述</th>
                  <th>类别</th>
                  <th>金额</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(transaction, index) in recentTransactions" :key="index">
                  <td>{{ formatDate(transaction.date) }}</td>
                  <td>{{ transaction.description }}</td>
                  <td>{{ transaction.category }}</td>
                  <td :class="transaction.amount < 0 ? 'expense' : 'income'">
                    ¥{{ Math.abs(transaction.amount).toFixed(2) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue';
import { useUserStore } from '../../store/user';
import { ElMessage, ElLoading } from 'element-plus';
import { Refresh } from '@element-plus/icons-vue';
import { getSpendingHabits } from '../../services/reports';
import axiosInstance from '../../services/axios';
import dayjs from 'dayjs';

// 状态变量
const isLoading = ref(true);
const isRefreshing = ref(false);
const error = ref(null);
const activeTab = ref('habits');
const activeAnalysisTab = ref('habits');
const dayChartRef = ref(null);
let dayChart = null;
const userStore = useUserStore();

// 数据引用
const spendingHabitsData = ref(null);
const aiAnalysis = ref({
  habits_analysis: '',
  financial_advice: ''
});
const basicStats = ref({
  totalSpending: 0,
  totalIncome: 0,
  averageTransaction: 0,
  transactionCount: 0
});
const spendingByDay = ref({});
const favoriteCategories = ref([]);
const recentTransactions = ref([]);

// 添加日期筛选
const dateRange = ref([
  dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
  dayjs().format('YYYY-MM-DD')
]);

// 计算属性：格式化后的分析文本
const formattedAnalysis = computed(() => {
  return formatText(aiAnalysis.value.habits_analysis || '');
});

// 计算属性：格式化后的财务建议
const formattedAdvice = computed(() => {
  return formatText(aiAnalysis.value.financial_advice || '');
});

// 计算属性：判断是否有数据
const hasData = computed(() => {
  // 检查AI分析数据是否存在
  const hasAiData = !!aiAnalysis.value.habits_analysis || !!aiAnalysis.value.financial_advice;
  console.log('是否有AI数据:', hasAiData, 'AI数据内容:', aiAnalysis.value);
  
  // 检查基础统计数据
  const hasBasicData = basicStats.value.totalSpending > 0 || 
                       basicStats.value.totalIncome > 0 || 
                       basicStats.value.transactionCount > 0;
  console.log('是否有基础数据:', hasBasicData, '基础数据:', basicStats.value);
  
  // 检查交易数据
  const hasTransactions = recentTransactions.value.length > 0;
  console.log('是否有交易数据:', hasTransactions, '交易条数:', recentTransactions.value.length);
  
  // 任何一种数据存在，就显示内容
  return hasAiData || hasBasicData || hasTransactions;
});

// 加载状态
const loading = ref(true);

// 将请求后端的函数独立出来，使用ai_format_template参数
const fetchSpendingHabitsData = async (startDate, endDate) => {
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (!token) throw new Error('未登录，请先登录');
  
  // 使用修改后的params调用
  const params = {
    start_date: startDate,
    end_date: endDate
  };
  
  // 直接使用axiosInstance调用API
  return await axiosInstance.get('/reports/spending-habits', { params });
};

// 处理后端返回的数据
const fetchData = async () => {
  error.value = null;
  loading.value = true;
  
  try {
    const startDate = dateRange.value?.[0] || undefined;
    const endDate = dateRange.value?.[1] || undefined;
    
    console.log('调用API，参数:', { startDate, endDate });
    const response = await fetchSpendingHabitsData(startDate, endDate);
    
    console.log('API响应数据(完整):', JSON.stringify(response.data));
    
    if (response.data) {
      // 直接使用后端返回的AI分析数据，不进行任何处理
      const aiData = response.data.ai_analysis || {};
      console.log('AI分析数据(详细):', JSON.stringify(aiData));
      
      aiAnalysis.value = {
        habits_analysis: aiData.habits_analysis || '',
        financial_advice: aiData.financial_advice || ''
      };
      
      // 提取基本统计和其他数据
      console.log('基本统计数据:', response.data.basic_stats);
      basicStats.value = {
        totalSpending: response.data.basic_stats?.total_spending || 0,
        totalIncome: response.data.basic_stats?.total_income || 0,
        averageTransaction: response.data.basic_stats?.average_transaction || 0,
        transactionCount: response.data.basic_stats?.transaction_count || 0
      };
      
      // 交易和图表数据
      recentTransactions.value = response.data.recent_transactions || [];
      spendingByDay.value = response.data.spending_by_day || {};
      favoriteCategories.value = response.data.favorite_categories || [];
      
      // 检查数据加载后的状态
      console.log('数据加载完成后, hasData =', hasData.value);
      
      // 渲染图表
      nextTick(() => {
        // 由于图表已被移除，不再需要初始化
        // 保留此函数但清空内容，以避免修改其他代码中的引用
      });
    } else {
      console.error('API响应中没有data字段');
    }
  } catch (err) {
    console.error("获取消费习惯分析失败:", err);
    error.value = "获取数据失败，请稍后重试";
  } finally {
    loading.value = false;
    isRefreshing.value = false;
  }
};

// 初始化所有图表
const initCharts = () => {
  // 由于图表已被移除，不再需要初始化
  // 保留此函数但清空内容，以避免修改其他代码中的引用
};

// 格式化文本，将Markdown格式转换为HTML
const formatText = (text) => {
  if (!text) return '';
  
  console.log("原始文本:", text);
  
  // 删除所有#标记（不论位置，包括单个#号）
  text = text.replace(/#{1,3}\s*\n?/g, '');
  text = text.replace(/\n?#{1,3}\s*/g, '');
  
  // 判断是否是财务建议
  const isFinancialAdvice = text.includes('财务改善建议') || text.includes('财务建议');
  
  // 移除开头的客套话（"尊敬的用户，我已经仔细分析了您的消费数据，让我为您做详细解读："等）
  text = text.replace(/^(尊敬的用户|亲爱的用户|用户您好).+解读：\s*/s, '');
  
  // 更彻底地移除"一、消费习惯分析"和"二、"标记
  text = text.replace(/一、\s*消费习惯分析\s*：?\s*/g, '');
  text = text.replace(/一、\s*消费习惯分析\s*/g, '');
  text = text.replace(/\n?二、\s*\n?/g, '');
  
  // 对消费习惯分析部分，移除顶部的"消费习惯分析"标题，因为UI中已经有这个标题
  if (!isFinancialAdvice) {
    text = text.replace(/^消费习惯分析\s*\n/g, '');
    text = text.replace(/^消费分析\s*\n/g, '');
  }
  
  // 根据不同类型处理标题
  if (isFinancialAdvice) {
    // 移除"财务改善建议："前缀，因为标题已经有了
    text = text.replace(/^.*?财务(改善)?建议：?\s*/s, '');
    // 再次检查开头是否仍有"财务改善建议"字样
    text = text.replace(/^财务(改善)?建议\s*/m, '');
  }
  
  // 先处理整体换行，保证段落分隔
  text = text.replace(/\n{3,}/g, '\n\n');
  
  console.log("清理后文本:", text);
  
  // 处理带有数字和点的项目（如"1. 调整娱乐和餐饮支出"）
  // 先处理特殊情况：财务改善建议1. xxx的格式
  // text = text.replace(/财务(改善)?建议(\d+)\.\s*(.*?)$/gm, '<div class="numbered-heading"><span class="number-badge">$2</span><span class="heading-content">$3</span></div>');
  
  // // 处理带有####标记的数字编号（如"#### 1. 内容"）
  // text = text.replace(/#{3,}\s*(\d+)\.\s+(.*?)$/gm, '<div class="numbered-heading"><span class="number-badge">$1</span><span class="heading-content">$2</span></div>');
  
  // // 处理普通的数字编号（如"1. 内容"）不带####
  // text = text.replace(/^(\d+)\.\s+(.*?)$/gm, '<div class="numbered-heading"><span class="number-badge">$1</span><span class="heading-content">$2</span></div>');
  
  // // 处理"# 数字. 内容"格式的标题
  // text = text.replace(/^#\s*(\d+)\.\s+(.*?)$/gm, '<div class="numbered-heading"><span class="number-badge">$1</span><span class="heading-content">$2</span></div>');
  
  // // 处理"# 章节名称"格式的标题
  // text = text.replace(/^#\s+(?!\d+\.)(.*?)$/gm, '<h3 class="analysis-title">$1</h3>');
  
  // // 处理所有可能的剩余Markdown标题
  // text = text.replace(/#{1,6}\s*(.*?)$/gm, '<h3 class="analysis-title">$1</h3>');
  
  // 处理段落
  const paragraphs = text.split('\n');
  let formattedText = '';
  let inList = false;
  
  for (let i = 0; i < paragraphs.length; i++) {
    const paragraph = paragraphs[i].trim();
    if (!paragraph) {
      // 空行结束列表
      if (inList) {
        inList = false;
      }
      continue;
    }
    
    // 已经有HTML标签的内容
    if (paragraph.includes('<h3') || paragraph.includes('<div') || paragraph.includes('<span')) {
      formattedText += paragraph + '\n';
      continue;
    }
    
    // 处理破折号或其他符号列表项（如"• 内容"或"- 内容"）
    if (/^[•\-]\s+/.test(paragraph)) {
      const content = paragraph.replace(/^[•\-]\s+(.*?)$/gm, 
        '<div class="simple-list-item">• $1</div>');
      formattedText += content + '\n';
      inList = true;
      continue;
    }
    
    // 普通段落，但是确保多行文本被正确连接
    if (!inList && i > 0 && !paragraphs[i-1].trim().endsWith('.') && 
        !paragraph.startsWith('#') && !paragraph.match(/^[•\-\d]/) && 
        paragraphs[i-1].trim() && !paragraphs[i-1].includes('<div')) {
      // 如果前一行不是以句号结束，且当前行不是标题或列表项，则视为同一段落的延续
      formattedText = formattedText.trimEnd();
      formattedText += ' ' + paragraph;
    } else {
      // 新段落
      formattedText += `<div class="simple-paragraph">${paragraph}</div>\n`;
    }
  }
  
  // 最后处理一些特殊格式（如粗体等）
  formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // 添加一个空行，确保底部有足够间距
  formattedText += '<div style="height: 20px;"></div>';
  
  console.log("格式化后的文本:", formattedText);
  
  return formattedText;
};

// 计算类别条形图宽度的百分比
const getCategoryBarWidth = (amount) => {
  if (!favoriteCategories.value.length) return '0%';
  
  const maxAmount = Math.max(...favoriteCategories.value.map(c => c.total_amount));
  if (maxAmount <= 0) return '0%';
  
  return `${(amount / maxAmount * 100)}%`;
};

// 格式化货币
const formatCurrency = (value) => {
  if (value === undefined || value === null) return '¥0.00';
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  }).format(value);
};

// 格式化数字
const formatNumber = (value) => {
  if (value === undefined || value === null) return '0';
  return new Intl.NumberFormat('zh-CN').format(value);
};

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}-${date.getDate()}`;
};

// 初始化日期并获取数据
const initDateAndFetch = () => {
  // 强制设置日期范围为最近30天
  dateRange.value = [
    dayjs().subtract(30, 'day').format('YYYY-MM-DD'),
    dayjs().format('YYYY-MM-DD')
  ];
  
  // 立即获取数据
  fetchData();
};

// 组件挂载时获取数据
onMounted(() => {
  initDateAndFetch();
});

// 监听窗口大小变化，更新图表
window.addEventListener('resize', () => {
  if (dayChart) {
    dayChart.resize();
  }
});
</script>

<style scoped>
.spending-habits-container {
  padding: 15px;
  max-width: 1200px;
  margin: 0 auto;
  background-color: #f0f8f5; /* 浅绿色背景 */
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.main-title {
  color: #3D6E59;
  font-size: 1.8rem;
  margin: 0;
  position: relative;
  padding-bottom: 8px;
}

.main-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 60px;
  height: 4px;
  background-color: #5DAF8E;
  border-radius: 2px;
}

.top-tabs {
  display: flex;
  background-color: #f8fffb; /* 更改为浅绿色背景 */
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(93, 175, 142, 0.1);
  margin-bottom: 15px;
}

.top-tab-item {
  flex: 1;
  text-align: center;
  padding: 10px;
  font-size: 1rem;
  cursor: pointer;
  color: #5DAF8E;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.top-tab-item.active {
  color: #3D6E59;
  background-color: #f0f8f5;
  border-bottom-color: #3D6E59;
  font-weight: 500;
}

.top-tab-item:hover:not(.active) {
  background-color: #f8fff8;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
}

.loading-spinner {
  border: 4px solid rgba(61, 110, 89, 0.1);
  border-radius: 50%;
  border-top: 4px solid #3D6E59;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #e74c3c;
  text-align: center;
  padding: 20px;
  background-color: #fdf3f2;
  border-radius: 8px;
  margin: 20px 0;
}

.analysis-container {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.card {
  background: #f8fffb; /* 更改为浅绿色背景 */
  border-radius: 8px;
  box-shadow: 0 1px 6px rgba(93, 175, 142, 0.12);
  margin-bottom: 15px;
  padding: 15px;
}

.card-title {
  color: #3D6E59;
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.1rem;
  font-weight: 500;
  border-bottom: 1px solid rgba(93, 175, 142, 0.15);
  padding-bottom: 8px;
}

.stats-card {
  grid-column: 1 / -1;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  padding: 20px;
}

.stat-item {
  background-color: #eaf7f1; /* 更浅的绿色背景 */
  border-radius: 8px;
  padding: 15px;
  text-align: center;
}

.stat-label {
  color: #5DAF8E;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.stat-value {
  color: #3D6E59;
  font-size: 1.5rem;
  font-weight: 600;
}

.analysis-card, .advice-card {
  grid-column: 1 / -1;
  background-color: #f8fffb; /* 更浅的绿色背景 */
}

.analysis-text {
  padding: 10px 15px;
  background-color: #f8fffb;
  border-radius: 6px;
}

.section-title {
  color: #3D6E59;
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 12px 0;
  text-align: center;
}

.chart-card {
  display: none; /* 隐藏图表卡片 */
}

.chart-container, .chart-wrapper, .chart {
  display: none; /* 隐藏图表容器 */
}

.transactions-card {
  grid-column: 1 / -1;
}

.transactions-table {
  width: 100%;
  border-collapse: collapse;
}

.transactions-table th {
  background-color: #eaf7f1;
  color: #3D6E59;
  text-align: left;
  padding: 12px 20px;
  font-weight: 600;
  border-bottom: 1px solid rgba(61, 110, 89, 0.2);
}

.transactions-table td {
  padding: 12px 20px;
  border-bottom: 1px solid rgba(61, 110, 89, 0.1);
}

.transactions-table tr:last-child td {
  border-bottom: none;
}

.expense {
  color: #e74c3c;
}

.income {
  color: #3D6E59;
}

@media (max-width: 600px) {
  .header-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .transactions-table {
    display: block;
    overflow-x: auto;
  }
}

.analysis-text :deep(.analysis-title) {
  color: #3D6E59;
  margin-top: 18px;
  margin-bottom: 10px;
  font-size: 1.25rem;
  font-weight: 600;
  border-bottom: 1px solid rgba(93, 175, 142, 0.1);
  padding-bottom: 8px;
}

.analysis-text :deep(.analysis-subtitle) {
  color: #3D6E59;
  margin-top: 16px;
  margin-bottom: 10px;
  font-size: 1.15rem;
  font-weight: 600;
  padding: 5px 0;
  border-bottom: 1px solid rgba(93, 175, 142, 0.1);
  display: flex;
  align-items: center;
}

.analysis-text :deep(.analysis-subtitle .section-number) {
  background-color: #3D6E59;
  color: white;
  font-size: 0.85rem;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 8px;
}

.analysis-text :deep(.analysis-section) {
  margin-bottom: 12px;
  position: relative;
  padding: 8px 12px;
  border-radius: 6px;
  background-color: rgba(93, 175, 142, 0.05);
  border-left: 3px solid rgba(93, 175, 142, 0.5);
}

.analysis-text :deep(.section-number) {
  color: #3D6E59;
  font-weight: 600;
  margin-right: 5px;
  padding: 1px 5px;
  background-color: rgba(93, 175, 142, 0.1);
  border-radius: 4px;
}

.analysis-text :deep(.analysis-paragraph) {
  margin-bottom: 10px;
  line-height: 1.6;
  color: #333;
  text-indent: 0;
  padding: 0 6px;
}

.analysis-text :deep(.analysis-list) {
  margin: 10px 0;
  padding: 8px 12px;
  list-style-type: none;
  background-color: rgba(93, 175, 142, 0.05);
  border-radius: 6px;
}

.analysis-text :deep(.analysis-item) {
  margin-bottom: 8px;
  position: relative;
  padding-left: 18px;
  line-height: 1.5;
}

.analysis-text :deep(.analysis-item)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 6px;
  height: 6px;
  background-color: #5DAF8E;
  border-radius: 50%;
}

.analysis-text :deep(.analysis-item.highlight-item) {
  background-color: rgba(93, 175, 142, 0.08);
  padding: 6px 10px 6px 20px;
  border-radius: 4px;
  margin-left: -10px;
}

.analysis-text :deep(.item-title) {
  color: #3D6E59;
  font-weight: 600;
  margin-right: 5px;
}

.analysis-text :deep(.advice-main-title),
.analysis-text :deep(.analysis-main-title) {
  display: none;
}

.analysis-text :deep(.number-section-title) {
  color: #3D6E59;
  margin: 16px 0 10px 0;
  padding: 8px 10px;
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  background-color: rgba(93, 175, 142, 0.08);
  border-radius: 6px;
  position: relative;
}

.analysis-text :deep(.number-section-title::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: #3D6E59;
  border-radius: 2px 0 0 2px;
}

.analysis-text :deep(.number-badge) {
  background-color: #3D6E59;
  color: white;
  font-size: 0.85rem;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 10px;
}

.simple-paragraph {
  margin-bottom: 12px;
  line-height: 1.5;
  color: #333;
}

.simple-item {
  margin-bottom: 8px;
  padding-left: 5px;
}

.item-number {
  color: #3D6E59;
  font-weight: 500;
  margin-right: 5px;
}

.simple-list-item {
  margin-bottom: 8px;
  padding-left: 5px;
  line-height: 1.5;
}

.highlight {
  color: #3D6E59;
  font-weight: 500;
}

.no-data-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
}

.no-data-icon {
  font-size: 3rem;
  margin-bottom: 15px;
  color: #5DAF8E;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 15px;
  color: #e74c3c;
}

.action-button, .retry-button {
  margin-top: 15px;
  padding: 8px 16px;
  background-color: #5DAF8E;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}

.retry-button {
  background-color: #e67e22;
}

.action-button:hover {
  background-color: #3D6E59;
}

.retry-button:hover {
  background-color: #d35400;
}

.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  color: #e74c3c;
  background-color: #fef5f5;
  border-radius: 8px;
  margin: 20px 0;
}

.numbered-heading {
  color: #3D6E59;
  margin: 16px 0 10px 0;
  padding: 8px 10px;
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  background-color: rgba(93, 175, 142, 0.08);
  border-radius: 6px;
  position: relative;
}

.numbered-heading::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: #3D6E59;
  border-radius: 2px 0 0 2px;
}

.number-badge {
  background-color: #3D6E59;
  color: white;
  font-size: 0.85rem;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 10px;
}

.heading-content {
  flex: 1;
}

.analysis-text :deep(.simple-paragraph) {
  margin-bottom: 12px;
  line-height: 1.5;
  color: #333;
}

.analysis-text :deep(.simple-item) {
  margin-bottom: 8px;
  padding-left: 5px;
}

.analysis-text :deep(.item-number) {
  color: #3D6E59;
  font-weight: 500;
  margin-right: 5px;
}

.analysis-text :deep(.simple-list-item) {
  margin-bottom: 8px;
  padding-left: 5px;
  line-height: 1.5;
}
</style> 