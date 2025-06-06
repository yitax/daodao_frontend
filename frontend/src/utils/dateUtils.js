import dayjs from 'dayjs';

/**
 * 获取今天的开始时间
 * @returns {Date} 今天的开始时间
 */
export function getStartOfToday() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    console.log('Start of today:', today);
    return today;
}

/**
 * 获取今天的结束时间
 * @returns {Date} 今天的结束时间
 */
export function getEndOfToday() {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    console.log('End of today:', today);
    return today;
}

/**
 * 获取本周的开始时间（周一）
 * @returns {Date} 本周的开始时间
 */
export function getStartOfThisWeek() {
    const today = new Date();
    const day = today.getDay(); // 0是周日，1-6是周一到周六

    // 计算与本周一的差距
    const diff = day === 0 ? 6 : day - 1;

    // 设置为本周一
    const monday = new Date(today);
    monday.setDate(today.getDate() - diff);
    monday.setHours(0, 0, 0, 0);

    console.log('Start of this week:', monday);
    return monday;
}

/**
 * 获取本周的结束时间（周日）
 * @returns {Date} 本周的结束时间
 */
export function getEndOfThisWeek() {
    const today = new Date();
    const day = today.getDay(); // 0是周日，1-6是周一到周六

    // 计算与本周日的差距
    const diff = day === 0 ? 0 : 7 - day;

    // 设置为本周日
    const sunday = new Date(today);
    sunday.setDate(today.getDate() + diff);
    sunday.setHours(23, 59, 59, 999);

    console.log('End of this week:', sunday);
    return sunday;
}

/**
 * 获取本月的开始时间
 * @returns {Date} 本月的开始时间
 */
export function getStartOfThisMonth() {
    const date = new Date();
    const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
    firstDay.setHours(0, 0, 0, 0);

    console.log('Start of this month:', firstDay);
    return firstDay;
}

/**
 * 获取本月的结束时间
 * @returns {Date} 本月的结束时间
 */
export function getEndOfThisMonth() {
    const date = new Date();
    // 下个月的第0天就是当月的最后一天
    const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    lastDay.setHours(23, 59, 59, 999);

    console.log('End of this month:', lastDay);
    return lastDay;
}

/**
 * 获取本年的开始时间
 * @returns {Date} 本年的开始时间
 */
export function getStartOfThisYear() {
    const date = new Date();
    const firstDay = new Date(date.getFullYear(), 0, 1); // 一月是0
    firstDay.setHours(0, 0, 0, 0);

    console.log('Start of this year:', firstDay);
    return firstDay;
}

/**
 * 获取本年的结束时间
 * @returns {Date} 本年的结束时间
 */
export function getEndOfThisYear() {
    const date = new Date();
    const lastDay = new Date(date.getFullYear(), 11, 31); // 十二月是11
    lastDay.setHours(23, 59, 59, 999);

    console.log('End of this year:', lastDay);
    return lastDay;
}

/**
 * 格式化日期为指定格式
 * @param {Date|string} date 日期对象或字符串
 * @param {string} format 格式化模式
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(date, format = 'YYYY-MM-DD') {
    return dayjs(date).format(format);
}

/**
 * 比较两个日期是否是同一天
 * @param {Date|string} date1 第一个日期
 * @param {Date|string} date2 第二个日期
 * @returns {boolean} 是否是同一天
 */
export function isSameDay(date1, date2) {
    const d1 = dayjs(date1);
    const d2 = dayjs(date2);
    return d1.format('YYYY-MM-DD') === d2.format('YYYY-MM-DD');
} 