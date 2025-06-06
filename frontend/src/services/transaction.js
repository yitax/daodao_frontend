import axiosInstance from './axios';

/**
 * 交易服务 - 提供与交易相关的API调用
 */
export default {
    /**
     * 获取交易列表
     * @param {Object} params - 查询参数
     * @returns {Promise} - 交易列表
     */
    async getTransactions(params = {}) {
        try {
            console.log('[TransactionService] 请求交易列表，参数:', params);

            // 处理日期过滤参数
            const queryParams = { ...params };

            // 处理filter_date参数（today/week/month）
            if (queryParams.filter_date) {
                const today = new Date();
                const todayStr = today.toISOString().split('T')[0];

                if (queryParams.filter_date === 'today') {
                    queryParams.start_date = todayStr;
                    queryParams.end_date = todayStr;
                }
                else if (queryParams.filter_date === 'week') {
                    // 计算本周一的日期
                    const dayOfWeek = today.getDay(); // 0是周日，1-6是周一至周六
                    const diffToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // 计算到周一的天数差

                    const mondayDate = new Date(today);
                    mondayDate.setDate(today.getDate() - diffToMonday);

                    queryParams.start_date = mondayDate.toISOString().split('T')[0];
                    queryParams.end_date = todayStr;
                }
                else if (queryParams.filter_date === 'month') {
                    // 本月第一天到今天
                    const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
                    queryParams.start_date = firstDayOfMonth.toISOString().split('T')[0];
                    queryParams.end_date = todayStr;
                }

                // 移除处理过的filter_date参数
                delete queryParams.filter_date;

                console.log('[TransactionService] 处理后的日期范围:',
                    queryParams.start_date, '到', queryParams.end_date);
            }

            const response = await axiosInstance.get('/transactions/', { params: queryParams });
            console.log('[TransactionService] 交易列表响应状态:', response.status);
            console.log('[TransactionService] 响应头:', response.headers);

            // 检查响应数据格式
            if (params.count_only && typeof response.data === 'object') {
                console.log('[TransactionService] 返回总数:', response.data);
                return response.data;
            }

            // 确保返回的是数组
            if (Array.isArray(response.data)) {
                console.log('[TransactionService] 返回交易记录数量:', response.data.length);
                return response.data;
            } else if (typeof response.data === 'object' && Array.isArray(response.data.items)) {
                // 某些API可能将结果包装在对象中
                console.log('[TransactionService] 返回嵌套交易记录数量:', response.data.items.length);
                return response.data.items;
            } else {
                console.warn('[TransactionService] 返回数据格式不符合预期:', response.data);
                return [];
            }
        } catch (error) {
            console.error('[TransactionService] 获取交易列表失败:', error);

            // 添加更多错误详情
            if (error.response) {
                console.error('- 响应状态:', error.response.status);
                console.error('- 响应数据:', error.response.data);
                console.error('- 响应头:', error.response.headers);
            } else if (error.request) {
                console.error('- 请求已发送但未收到响应');
            } else {
                console.error('- 请求配置错误:', error.message);
            }

            throw error;
        }
    },

    /**
     * 获取单个交易详情
     * @param {Number} id - 交易ID
     * @returns {Promise} - 交易详情
     */
    async getTransaction(id) {
        try {
            const response = await axiosInstance.get(`/transactions/${id}/`);
            return response.data;
        } catch (error) {
            console.error(`获取交易ID=${id}失败:`, error);
            throw error;
        }
    },

    /**
     * 创建新交易
     * @param {Object} transaction - 交易数据
     * @returns {Promise} - 创建的交易
     */
    async createTransaction(transaction) {
        try {
            const response = await axiosInstance.post('/transactions/', transaction);
            return response.data;
        } catch (error) {
            console.error('创建交易失败:', error);
            throw error;
        }
    },

    /**
     * 更新交易
     * @param {Number} id - 交易ID
     * @param {Object} transaction - 要更新的交易数据
     * @returns {Promise} - 更新后的交易
     */
    async updateTransaction(id, transaction) {
        try {
            const response = await axiosInstance.put(`/transactions/${id}/`, transaction);
            return response.data;
        } catch (error) {
            console.error(`更新交易ID=${id}失败:`, error);
            throw error;
        }
    },

    /**
     * 删除交易
     * @param {Number} id - 要删除的交易ID
     * @returns {Promise}
     */
    async deleteTransaction(id) {
        try {
            await axiosInstance.delete(`/transactions/${id}/`);
            return true;
        } catch (error) {
            console.error(`删除交易ID=${id}失败:`, error);
            throw error;
        }
    },

    /**
     * 获取今日交易
     * @returns {Promise} - 今日交易列表
     */
    async getTodayTransactions() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const response = await axiosInstance.get('/transactions/', {
                params: {
                    start_date: today,
                    end_date: today,
                    limit: 100 // 假设今天的交易不会超过100条
                }
            });
            return response.data;
        } catch (error) {
            console.error('获取今日交易失败:', error);
            throw error;
        }
    },

    /**
     * 获取最近交易
     * @param {Number} days - 最近几天
     * @param {Number} limit - 限制条数
     * @returns {Promise} - 最近交易列表
     */
    async getRecentTransactions(days = 7, limit = 20) {
        try {
            const today = new Date();
            const pastDate = new Date();
            pastDate.setDate(today.getDate() - days);

            const response = await axiosInstance.get('/transactions', {
                params: {
                    start_date: pastDate.toISOString().split('T')[0],
                    end_date: today.toISOString().split('T')[0],
                    limit: limit
                }
            });
            return response.data;
        } catch (error) {
            console.error(`获取最近${days}天交易失败:`, error);
            throw error;
        }
    },

    /**
     * 按交易类型获取交易
     * @param {String} type - 交易类型 income或expense
     * @param {Object} params - 其他查询参数
     * @returns {Promise} - 交易列表
     */
    async getTransactionsByType(type, params = {}) {
        try {
            const queryParams = { ...params, transaction_type: type };
            const response = await axiosInstance.get('/transactions', { params: queryParams });
            return response.data;
        } catch (error) {
            console.error(`获取${type}类型交易失败:`, error);
            throw error;
        }
    },

    /**
     * 按类别获取交易
     * @param {String} category - 交易类别
     * @param {Object} params - 其他查询参数
     * @returns {Promise} - 交易列表
     */
    async getTransactionsByCategory(category, params = {}) {
        try {
            const queryParams = { ...params, category: category };
            const response = await axiosInstance.get('/transactions', { params: queryParams });
            return response.data;
        } catch (error) {
            console.error(`获取${category}类别交易失败:`, error);
            throw error;
        }
    }
}; 