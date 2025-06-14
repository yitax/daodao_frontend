<template>
  <div class="manual-entry">
    <!-- 移除调试面板和登录提示，保持界面整洁 -->

    <div class="top-actions">
      <el-button 
        type="success" 
        @click="openDialog('create')" 
        :icon="Plus" 
        circle 
        class="add-transaction-btn"
      ></el-button>
      <div class="filters">
        <el-select v-model="timeFilter" placeholder="时间筛选" @change="loadTransactions(true)" style="width: 120px">
          <el-option label="今天" value="today"></el-option>
          <el-option label="本周" value="week"></el-option>
          <el-option label="本月" value="month"></el-option>
          <el-option label="所有" value="all"></el-option>
        </el-select>
        <el-select v-model="typeFilter" placeholder="类型筛选" @change="loadTransactions(true)" style="width: 120px">
          <el-option label="全部" value=""></el-option>
          <el-option label="收入" value="income"></el-option>
          <el-option label="支出" value="expense"></el-option>
        </el-select>
      </div>
    </div>

    <!-- 交易列表 -->
    <el-card shadow="hover" class="transaction-list" :body-style="{padding: '0px'}">
      <template #header>
        <div class="card-header">
          <h3>交易记录</h3>
          <div class="filter-tag" v-if="timeFilter !== 'all'">
            筛选时间：{{ getTimeFilterLabel() }}
          </div>
        </div>
      </template>
      <el-table 
        :data="transactions" 
        style="width: 100%" 
        v-loading="loading"
        :header-cell-style="{
          backgroundColor: '#E3F2ED', 
          color: '#3D6E59',
          fontWeight: 'bold'
        }"
        :row-class-name="tableRowClassName"
        stripe
      >
        <el-table-column label="日期" width="100">
          <template #default="{ row }">
            {{ format(parseISO(row.transaction_date), 'yyyy-MM-dd') }}
          </template>
        </el-table-column>
        <el-table-column label="时间" width="100">
          <template #default="{ row }">
            {{ row.transaction_time ? format(parseISO(row.transaction_time), 'HH:mm') : '未设置' }}
          </template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === 'income' ? 'success' : 'danger'" size="small" effect="dark">
              {{ row.type === 'income' ? '收入' : '支出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span :class="row.type === 'income' ? 'income-amount' : 'expense-amount'">
              {{ row.type === 'income' ? '+' : '-' }} {{ row.amount.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="类别" width="120">
          <template #default="{ row }">
            {{ row.category }}
          </template>
        </el-table-column>
        <el-table-column label="描述">
          <template #default="{ row }">
            {{ row.description }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="operation-btns">
              <el-button size="small" type="primary" :icon="Edit" circle @click="openDialog('edit', row)" class="edit-btn"></el-button>
              <el-button size="small" type="danger" :icon="Delete" circle @click="confirmDelete(row)"></el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页控件 -->
      <div class="pagination" v-if="total > 0">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
        ></el-pagination>
      </div>

      <!-- 无数据提示 -->
      <el-empty v-if="transactions.length === 0 && !loading" description="暂无交易记录"></el-empty>
    </el-card>

    <!-- 交易表单对话框 -->
    <el-dialog
      :title="dialogMode === 'create' ? '添加交易' : '编辑交易'"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form label-width="100px" :model="transactionForm">
        <el-form-item label="交易类型">
          <el-radio-group v-model="transactionForm.type">
            <el-radio label="expense">支出</el-radio>
            <el-radio label="income">收入</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="金额">
          <el-input v-model="transactionForm.amount" type="number" placeholder="请输入金额"></el-input>
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="transactionForm.category" placeholder="选择类别" style="width: 100%">
            <el-option-group label="支出类别" v-if="transactionForm.type === 'expense'">
              <el-option label="餐饮美食" value="餐饮美食"></el-option>
              <el-option label="交通出行" value="交通出行"></el-option>
              <el-option label="服饰美容" value="服饰美容"></el-option>
              <el-option label="日用百货" value="日用百货"></el-option>
              <el-option label="住房物业" value="住房物业"></el-option>
              <el-option label="医疗健康" value="医疗健康"></el-option>
              <el-option label="文教娱乐" value="文教娱乐"></el-option>
              <el-option label="人情往来" value="人情往来"></el-option>
              <el-option label="其他支出" value="其他支出"></el-option>
            </el-option-group>
            <el-option-group label="收入类别" v-if="transactionForm.type === 'income'">
              <el-option label="工资薪酬" value="工资薪酬"></el-option>
              <el-option label="投资理财" value="投资理财"></el-option>
              <el-option label="奖金" value="奖金"></el-option>
              <el-option label="退款" value="退款"></el-option>
              <el-option label="兼职收入" value="兼职收入"></el-option>
              <el-option label="租金收入" value="租金收入"></el-option>
              <el-option label="礼金收入" value="礼金收入"></el-option>
              <el-option label="中奖收入" value="中奖收入"></el-option>
              <el-option label="意外所得" value="意外所得"></el-option>
              <el-option label="其他收入" value="其他收入"></el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="transactionForm.transaction_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            :default-value="new Date()"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="时间">
          <el-time-picker
            v-model="transactionForm.transaction_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择时间"
            style="width: 100%"
            :default-value="new Date()"
          ></el-time-picker>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="transactionForm.description"
            type="textarea"
            placeholder="请输入交易描述"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="saveTransaction"
            :loading="submitting"
            >提交</el-button
          >
        </span>
      </template>
    </el-dialog>

    <!-- 删除确认 -->
    <el-dialog
      title="确认删除"
      v-model="deleteConfirmVisible"
      width="300px"
    >
      <p>确定要删除这条交易记录吗？</p>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteConfirmVisible = false">取消</el-button>
          <el-button
            type="danger"
            @click="deleteTransaction"
            :loading="deleting"
            >删除</el-button
          >
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import transactionService from '../services/transaction'
import axiosInstance from '../services/axios'
import { format, parseISO, isToday, formatDistance } from 'date-fns'
import { zhCN } from 'date-fns/locale' 

// State variables
const transactions = ref([])
const todayTransactions = ref([])
const loading = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('create')
const deleteConfirmVisible = ref(false)
const transactionToDelete = ref(null)
const currentTransactionId = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const timeFilter = ref('today')
const typeFilter = ref('')
const activeDebugPanel = ref(['1']) // 默认展开调试面板
const lastQueryParams = ref({})

// Form data
const transactionForm = ref({
  type: 'expense',
  amount: '',
  description: '',
  category: '',
  transaction_date: new Date().toISOString().split('T')[0],
  transaction_time: format(new Date(), 'HH:mm')
})

// 重置表单
const resetForm = () => {
  transactionForm.value = {
    type: 'expense',
    amount: '',
    description: '',
    category: '',
    transaction_date: new Date().toISOString().split('T')[0],
    transaction_time: format(new Date(), 'HH:mm')
  }
}

// 打开对话框
const openDialog = (mode, transaction) => {
  dialogMode.value = mode
  if (mode === 'create') {
    resetForm()
  } else {
    // 填充表单数据
    currentTransactionId.value = transaction.id
    
    // 处理日期和时间
    let txDate = transaction.transaction_date
    let txTime = null
    
    // 确保日期格式正确
    if (txDate && typeof txDate === 'string') {
      // 如果是ISO格式的日期时间，只获取日期部分
      if (txDate.includes('T')) {
        txDate = txDate.split('T')[0]
      }
    }
    
    // 处理时间
    if (transaction.transaction_time) {
      try {
        // 尝试将ISO格式的日期时间转换为只有时间部分
        const timeDate = new Date(transaction.transaction_time)
        txTime = format(timeDate, 'HH:mm')
      } catch (error) {
        console.error('时间格式转换失败:', error)
        txTime = format(new Date(), 'HH:mm')
      }
    } else {
      txTime = format(new Date(), 'HH:mm')
    }
    
    console.log('编辑交易:', {
      原始日期: transaction.transaction_date,
      处理后日期: txDate,
      原始时间: transaction.transaction_time,
      处理后时间: txTime,
      原始类型: transaction.type
    })
    
    // 确保类型值正确映射
    const mappedType = transaction.type === 'INCOME' || transaction.type === 'income' ? 'income' : 'expense'
    
    transactionForm.value = {
      type: mappedType,
      amount: transaction.amount,
      description: transaction.description || '',
      category: transaction.category || '',
      transaction_date: txDate,
      transaction_time: txTime
    }
  }
  dialogVisible.value = true
}

// 确认删除
const confirmDelete = (transaction) => {
  transactionToDelete.value = transaction
  deleteConfirmVisible.value = true
}

// 处理页面变化
const handlePageChange = (page) => {
  currentPage.value = page
  loadTransactions(false)
}

// 获取时间筛选标签
const getTimeFilterLabel = () => {
  const map = {
    'today': '今天',
    'week': '本周',
    'month': '本月',
    'all': '所有'
  }
  return map[timeFilter.value] || '未知'
}

// 表格行样式
const tableRowClassName = ({ row, rowIndex }) => {
  const today = new Date().toISOString().split('T')[0]
  if (row.transaction_date === today) {
    return 'today-row'
  }
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}

// 加载交易记录（修改日期处理逻辑）
const loadTransactions = async (resetPage = true) => {
  if (resetPage) {
    currentPage.value = 1
  }
  
  loading.value = true
  try {
    // 准备当前日期相关值
    const today = new Date();
    const todayStr = formatDate(today);
    
    // 准备周一日期
    const mondayDate = getMonday();
    const mondayStr = formatDate(mondayDate);
    
    // 准备月初日期
    const firstDayOfMonth = getFirstDayOfMonth();
    const firstDayStr = formatDate(firstDayOfMonth);
    
    // 构建查询参数
    let params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    }
    
    // 直接设置精确的日期参数
    if (timeFilter.value === 'today') {
      // 今天: 使用相同的开始和结束日期
      params.start_date = todayStr;
      params.end_date = todayStr;
      console.log(`筛选今天: ${todayStr}`);
    } 
    else if (timeFilter.value === 'week') {
      // 本周: 从周一到今天
      params.start_date = mondayStr;
      params.end_date = todayStr;
      console.log(`筛选本周: ${mondayStr} 至 ${todayStr}`);
    } 
    else if (timeFilter.value === 'month') {
      // 本月: 从月初到今天
      params.start_date = firstDayStr;
      params.end_date = todayStr;
      console.log(`筛选本月: ${firstDayStr} 至 ${todayStr}`);
    } else {
      console.log('查询所有记录');
    }
    
    // 添加类型筛选
    if (typeFilter.value) {
      params.transaction_type = typeFilter.value;
      console.log('类型筛选:', params.transaction_type);
    }
    
    console.log('API查询参数:', params);
    lastQueryParams.value = {...params}; // 保存查询参数用于调试
    
    // 直接使用axios实例发送请求，绕过服务层的日期处理
    const response = await axiosInstance.get('/transactions/', { params });
    console.log('API响应:', response);
    
    // 处理响应数据
    if (Array.isArray(response.data)) {
      console.log(`获取到${response.data.length}条交易记录`);
      // 后端已经使用小写的income/expense，不需要转换
      transactions.value = response.data;
    } else {
      console.warn('API返回的不是数组:', response.data);
      transactions.value = [];
    }
    
    // 获取总计数量 - 使用新的方法，不依赖服务层
    const countParams = { ...params, limit: 0, count_only: true };
    const countResponse = await axiosInstance.get('/transactions/', { params: countParams });
    
    if (typeof countResponse.data === 'object' && countResponse.data.hasOwnProperty('total')) {
      total.value = countResponse.data.total;
    } else if (Array.isArray(transactions.value)) {
      total.value = transactions.value.length;
    } else {
      total.value = 0;
    }
    
    console.log('总记录数:', total.value);
    
  } catch (error) {
    console.error('加载交易记录失败:', error);
    ElMessage.error('加载交易记录失败，请重试');
  } finally {
    loading.value = false;
  }
}

// 保存交易
const saveTransaction = async () => {
  const formEl = document.querySelector('.el-form')
  if (!formEl) return
  
  try {
    submitting.value = true
    
    // 检查必填字段
    if (!transactionForm.value.amount) {
      ElMessage.error('请输入金额')
      submitting.value = false
      return
    }
    
    if (!transactionForm.value.category) {
      ElMessage.error('请选择类别')
      submitting.value = false
      return
    }
    
    // 构建提交数据
    const data = {
      type: transactionForm.value.type, // 直接使用前端的income/expense，不需要转换
      amount: Number(transactionForm.value.amount),
      description: transactionForm.value.description || '无',  // 确保描述不为空
      category: transactionForm.value.category,
      transaction_date: transactionForm.value.transaction_date,
      // 修复transaction_time格式问题，确保年份是实际年份而不是yyyy占位符
      transaction_time: transactionForm.value.transaction_time ? 
        `${transactionForm.value.transaction_date}T${transactionForm.value.transaction_time}:00` : null,
      currency: 'CNY'
    }
    
    // 调试日期和时间值
    console.log('日期值:', transactionForm.value.transaction_date)
    console.log('时间值:', transactionForm.value.transaction_time)
    console.log('合并后的datetime:', data.transaction_time)
    
    // 确保日期格式正确
    if (data.transaction_date && data.transaction_date.includes('yyyy')) {
      // 如果日期中包含占位符，替换为实际年份
      const currentYear = new Date().getFullYear()
      data.transaction_date = data.transaction_date.replace('yyyy', currentYear)
      console.log('修正后的日期:', data.transaction_date)
    }
    
    // 确保时间格式正确
    if (data.transaction_time && data.transaction_time.includes('yyyy')) {
      // 如果时间中包含占位符，替换为实际年份
      const currentYear = new Date().getFullYear()
      data.transaction_time = data.transaction_time.replace('yyyy', currentYear)
      console.log('修正后的时间:', data.transaction_time)
    }
    
    console.log('发送的交易数据:', JSON.stringify(data, null, 2))
    
    let response
    
    if (dialogMode.value === 'create') {
      // 创建新交易
      console.log('创建新交易...')
      try {
        response = await axiosInstance.post('/transactions/', data)
        console.log('创建交易成功:', response.data)
        ElMessage.success('交易已成功添加')
      } catch (postError) {
        console.error('创建交易错误详情:', postError)
        if (postError.response) {
          console.error('响应状态码:', postError.response.status)
          console.error('响应头:', postError.response.headers)
          console.error('响应数据:', JSON.stringify(postError.response.data, null, 2))
        }
        throw postError // 重新抛出以便被外层catch捕获
      }
    } else {
      // 更新现有交易
      console.log('更新交易...')
      try {
        response = await axiosInstance.put(`/transactions/${currentTransactionId.value}/`, data)
        console.log('更新交易成功:', response.data)
        ElMessage.success('交易已成功更新')
      } catch (putError) {
        console.error('更新交易错误详情:', putError)
        if (putError.response) {
          console.error('响应状态码:', putError.response.status)
          console.error('响应头:', putError.response.headers)
          console.error('响应数据:', JSON.stringify(putError.response.data, null, 2))
        }
        throw putError // 重新抛出以便被外层catch捕获
      }
    }
    
    dialogVisible.value = false
    loadTransactions() // 重新加载数据
    
  } catch (error) {
    console.error('保存交易失败:', error)
    if (error.response) {
      console.error('响应状态:', error.response.status)
      console.error('响应数据:', error.response.data)
      
      // 改进错误信息处理
      let errorMsg = '保存失败: '
      
      // 处理可能的嵌套错误结构
      const formatErrorObject = (errorObj) => {
        if (!errorObj) return '未知错误';
        
        if (typeof errorObj === 'string') return errorObj;
        
        if (Array.isArray(errorObj)) {
          return errorObj.map(item => formatErrorObject(item)).join(', ');
        }
        
        if (typeof errorObj === 'object') {
          const details = [];
          for (const key in errorObj) {
            const value = formatErrorObject(errorObj[key]);
            details.push(`${key}: ${value}`);
          }
          return details.join('; ');
        }
        
        return String(errorObj);
      };

      if (error.response.data) {
        if (error.response.data.detail) {
          // 处理嵌套的detail对象
          errorMsg += formatErrorObject(error.response.data.detail);
        } else {
          // 处理整个响应对象
          errorMsg += formatErrorObject(error.response.data);
        }
      } else {
        errorMsg += '服务器错误，请稍后重试';
      }
      
      ElMessage.error(errorMsg)
    } else {
      ElMessage.error(`保存失败: ${error.message || '网络错误'}`)
    }
  } finally {
    submitting.value = false
  }
}

// 删除交易
const deleteTransaction = async () => {
  if (!transactionToDelete.value) return
  
  try {
    deleting.value = true
    await transactionService.deleteTransaction(transactionToDelete.value.id)
    ElMessage.success('交易已删除')
    deleteConfirmVisible.value = false
    loadTransactions() // 重新加载数据
  } catch (error) {
    console.error('删除交易失败:', error)
    ElMessage.error(`删除失败: ${error.response?.data?.detail || '未知错误'}`)
  } finally {
    deleting.value = false
  }
}

// 监听筛选器变化
watch([timeFilter, typeFilter], () => {
  loadTransactions(true)
})

// 格式化日期helper函数
const formatDate = (date) => {
  return format(date, 'yyyy-MM-dd')
}

// 获取本周一
const getMonday = () => {
  const today = new Date()
  const dayOfWeek = today.getDay() // 0是周日，1-6是周一至周六
  const diffToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1 // 计算到周一的天数差
  
  const mondayDate = new Date(today)
  mondayDate.setDate(today.getDate() - diffToMonday)
  
  return mondayDate
}

// 获取本月第一天
const getFirstDayOfMonth = () => {
  const today = new Date()
  return new Date(today.getFullYear(), today.getMonth(), 1)
}

// 强制刷新
const forceRefresh = () => {
  loadTransactions(true)
  ElMessage.success('强制刷新数据')
}

// Lifecycle hooks
onMounted(() => {
  loadTransactions()
})
</script>

<style scoped>
/* 修改样式，使用薄荷绿主题 */
.manual-entry {
  padding: 20px;
}

.top-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.add-transaction-btn {
  width: 56px !important;
  height: 56px !important;
  font-size: 24px !important;
  background-color: #3D6E59 !important; /* 使用薄荷绿主题色 */
  border-color: #3D6E59 !important;
  box-shadow: 0 4px 12px rgba(61, 110, 89, 0.4);
}

.add-transaction-btn:hover {
  background-color: #4E8C71 !important; /* 悬停时稍亮一些 */
  border-color: #4E8C71 !important;
}

.filters {
  display: flex;
  gap: 10px;
}

.transaction-list {
  margin-bottom: 20px;
  border: 1px solid #C6F7E2;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #E3F2ED;
  padding: 10px 15px;
}

.card-header h3 {
  margin: 0;
  color: #3D6E59;
}

.filter-tag {
  background-color: #3D6E59;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  padding-bottom: 20px;
}

.income-amount {
  color: #3D6E59;
  font-weight: bold;
}

.expense-amount {
  color: #f56c6c;
  font-weight: bold;
}

.operation-btns {
  display: flex;
  gap: 10px;
}

.edit-btn {
  background-color: #3D6E59 !important;
  border-color: #3D6E59 !important;
}

.edit-btn:hover {
  background-color: #4E8C71 !important;
  border-color: #4E8C71 !important;
}

/* 调试面板 */
.debug-panel {
  margin-bottom: 20px;
  border: 1px dashed #3D6E59;
  border-radius: 4px;
}

.debug-content {
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
}

.debug-content h4 {
  margin-top: 10px;
  margin-bottom: 5px;
  color: #3D6E59;
}

.debug-content pre {
  background-color: #f0f0f0;
  padding: 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

:deep(.today-row) {
  background-color: #e0f7ed !important;
}

:deep(.even-row) {
  background-color: #f9fffc;
}

:deep(.odd-row) {
  background-color: #ffffff;
}

:deep(.el-table th) {
  font-weight: bold !important;
}

:deep(.el-table) {
  --el-table-border-color: #C6F7E2;
  --el-table-header-bg-color: #E3F2ED;
}

:deep(.el-card__header) {
  padding: 0;
  border-bottom: 2px solid #C6F7E2;
}

:deep(.el-pagination.is-background .el-pager li:not(.disabled).active) {
  background-color: #3D6E59;
}
</style> 