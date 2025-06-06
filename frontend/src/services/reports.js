import axiosInstance from './axios';

// 获取消费习惯分析
export const getSpendingHabits = (startDate, endDate, options = {}) => {
    let params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    // 添加其他可选参数
    if (options.ai_format_template) {
        params.ai_format_template = options.ai_format_template;
    }

    return axiosInstance.get('/reports/spending-habits', { params });
};

// 获取总收支概览
export const getSummary = (startDate, endDate) => {
    let params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return axiosInstance.get('/reports/summary', { params });
};

// 获取每日收支趋势
export const getDailyTrend = (startDate, endDate) => {
    let params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return axiosInstance.get('/reports/daily', { params });
};

// 获取分类排行
export const getCategoryRanking = (transactionType, startDate, endDate) => {
    let params = { transaction_type: transactionType };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return axiosInstance.get('/reports/category-ranking', { params });
};

// 获取交易排行
export const getTransactionRanking = (transactionType, startDate, endDate, limit = 20, category = null) => {
    let params = {
        transaction_type: transactionType,
        limit
    };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (category) params.category = category;
    return axiosInstance.get('/reports/transaction-ranking', { params });
};

// 获取账本明细
export const getLedger = (params) => {
    return axiosInstance.get('/reports/ledger', { params });
}; 