from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract, case
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import calendar
import os
import openai
import json
import traceback
from dotenv import load_dotenv

from ..models.models import Transaction, User, TransactionType

# 加载环境变量
load_dotenv()

# 初始化OpenAI API
openai.api_key = os.getenv("API_KEY")
openai.api_base = os.getenv("API_URL")
use_model="gemini-2.5-flash-preview-05-20-thinking"
# 设置默认请求配置，关闭超时
openai.api_requestor.TIMEOUT_SECS = None


class SpendingHabitsAnalyzer:
    """分析用户消费习惯的服务类"""

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db

    def get_basic_stats(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取用户基本消费统计信息"""
        # 1. 计算总的交易次数
        query = self.db.query(func.count(Transaction.id)).filter(
            Transaction.user_id == self.user_id, Transaction.is_deleted == False
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        total_transactions = query.scalar() or 0

        # 2. 最早的交易日期
        query = self.db.query(func.min(Transaction.transaction_date)).filter(
            Transaction.user_id == self.user_id, Transaction.is_deleted == False
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        first_transaction = query.scalar()

        # 3. 最近的交易日期
        query = self.db.query(func.max(Transaction.transaction_date)).filter(
            Transaction.user_id == self.user_id, Transaction.is_deleted == False
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        latest_transaction = query.scalar()

        # 4. 计算总支出
        query = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.EXPENSE,
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        total_expense = query.scalar() or 0

        # 5. 计算总收入
        query = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.INCOME,
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        total_income = query.scalar() or 0

        days_period = 1  # 默认为1天，避免除以零
        if first_transaction and latest_transaction:
            delta = (latest_transaction - first_transaction).days + 1
            days_period = max(1, delta)  # 确保至少是1天

        avg_daily_expense = total_expense / days_period if days_period > 0 else 0

        # 5. 计算平均收入和支出
        query_income = self.db.query(func.avg(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.INCOME,
        )

        # 添加日期过滤条件
        if start_date:
            query_income = query_income.filter(
                Transaction.transaction_date >= start_date
            )
        if end_date:
            query_income = query_income.filter(Transaction.transaction_date <= end_date)

        avg_income = query_income.scalar() or 0

        query_expense = self.db.query(func.avg(Transaction.amount)).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.EXPENSE,
        )

        # 添加日期过滤条件
        if start_date:
            query_expense = query_expense.filter(
                Transaction.transaction_date >= start_date
            )
        if end_date:
            query_expense = query_expense.filter(
                Transaction.transaction_date <= end_date
            )

        avg_expense = query_expense.scalar() or 0

        transaction_count = total_transactions

        return {
            "total_spending": total_expense,
            "total_income": total_income,
            "average_transaction": avg_expense,
            "transaction_count": transaction_count,
            "first_transaction_date": first_transaction,
            "latest_transaction_date": latest_transaction,
            "avg_daily_expense": round(avg_daily_expense, 2),
        }

    def get_spending_pattern_by_day(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """分析用户按星期几的消费模式"""
        # 使用extract函数获取星期几（1-7，其中1是星期一，7是星期日）
        query = self.db.query(
            extract("dow", Transaction.transaction_date).label("day_of_week"),
            func.sum(Transaction.amount).label("total_amount"),
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.EXPENSE,
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        day_pattern = query.group_by("day_of_week").order_by("day_of_week").all()

        # 将结果转换为字典，星期几为键，总金额为值
        # 注意：SQLite的星期几是0-6，0是星期日，所以需要调整
        result = {}
        days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
        for day_of_week, total_amount in day_pattern:
            # 调整为我们的星期几格式（0是周日）
            adjusted_day = days[day_of_week]
            result[adjusted_day] = round(total_amount, 2)

        # 确保所有星期几都有值
        for day in days:
            if day not in result:
                result[day] = 0.0

        return result

    def get_favorite_categories(
        self,
        limit: int = 5,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """获取用户最常消费的类别"""
        query = self.db.query(
            Transaction.category,
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total_amount"),
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.EXPENSE,
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        favorite_categories = (
            query.group_by(Transaction.category)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )

        return [
            {
                "category": category,
                "count": count,
                "total_amount": round(total_amount, 2),
            }
            for category, count, total_amount in favorite_categories
        ]

    def get_monthly_spending_trend(
        self,
        months: int = 6,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """获取用户最近几个月的消费趋势"""
        today = date.today()

        # 如果没有提供开始日期，设置为今天减去指定的月数
        if not start_date:
            start_month = today.month - months + 1
            start_year = today.year

            # 如果start_month为负数或0，调整年份和月份
            if start_month <= 0:
                start_year -= 1
                start_month = 12 + start_month

            # 创建开始日期
            start_date = date(start_year, start_month, 1)

        # 如果没有提供结束日期，设置为今天
        if not end_date:
            end_date = today

        # 获取每月支出总额
        query = self.db.query(
            extract("year", Transaction.transaction_date).label("year"),
            extract("month", Transaction.transaction_date).label("month"),
            func.sum(Transaction.amount).label("total_amount"),
        ).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.EXPENSE,
        )

        # 添加日期过滤条件
        query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        monthly_spending = (
            query.group_by("year", "month").order_by("year", "month").all()
        )

        # 准备结果数组
        result = []

        # 计算需要显示的月份数
        if start_date and end_date:
            months = (
                (end_date.year - start_date.year) * 12
                + end_date.month
                - start_date.month
                + 1
            )

        for i in range(months):
            # 计算当前月份
            curr_month = (start_date.month + i - 1) % 12 + 1  # 调整范围为1-12
            curr_year = start_date.year + (start_date.month + i - 1) // 12

            # 默认该月支出为0
            month_data = {
                "year": curr_year,
                "month": curr_month,
                "month_name": calendar.month_name[curr_month],
                "total_amount": 0.0,
            }

            # 查找该月的实际支出
            for year, month, amount in monthly_spending:
                if year == curr_year and month == curr_month:
                    month_data["total_amount"] = round(amount, 2)
                    break

            result.append(month_data)

        return result

    def get_recent_transactions(
        self,
        limit: int = 10,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """获取用户最近的交易记录"""
        query = self.db.query(Transaction).filter(
            Transaction.user_id == self.user_id,
            Transaction.is_deleted == False,
        )

        # 添加日期过滤条件
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        recent_transactions = (
            query.order_by(Transaction.transaction_date.desc()).limit(limit).all()
        )

        return [
            {
                "id": tx.id,
                "type": tx.type,
                "amount": tx.amount,
                "description": tx.description,
                "category": tx.category,
                "date": tx.transaction_date,
                "currency": tx.currency,
                "is_income": tx.type == TransactionType.INCOME,
            }
            for tx in recent_transactions
        ]


def generate_ai_analysis(spending_data: Dict[str, Any]) -> Dict[str, Any]:
    """使用AI生成消费习惯分析和建议"""
    print("\n***** 开始生成AI消费分析 *****")

    try:
        # 将数据转换为JSON字符串，以便在提示中使用
        spending_json = json.dumps(spending_data, indent=2, default=str)

        # 构建详细的提示
        prompt = f"""
        我需要你帮用户分析他的消费习惯并提供合理的财务建议。以下是用户的消费数据，用您来称呼用户:

        ```json
        {spending_json}
        ```

        请根据以上数据进行深入分析，包括但不限于：
        1. 消费习惯分析：基于消费类别、时间模式和金额特征
        2. 异常消费模式识别：是否有不寻常的消费行为
        3. 财务健康评估：基于收入与支出比例
        4. 节约潜力指出：哪些类别可以减少开支
        5. 具体的改善建议：实用且易于执行的建议

        将你的回答分为两部分，大标题必须严格是这两个，不要有其他名字标题,严格分点回答，要换行：
        1. 消费习惯分析：详细分析用户当前的消费模式和特点（4-6条小标题）
        2. 财务改善建议：4-6条具体的改善建议
        
        示例格式：
        (前面和结尾不要有任何输出）
        一、消费习惯分析
            1. ***
            2. ***
        二、财务改善建议
            1. ***
            2. ***
        严格按照此格式，在此之外不要有其他任何输出。
        请使用友好、专业的语气，避免过于生硬或说教的口吻。回答必须是中文。
        """

        print("调用AI API进行消费分析...")

        # 调用API (不设置超时)
        response = openai.ChatCompletion.create(
            model=use_model,
            messages=[
                {
                    "role": "assistant",
                    "content": "你是一位专业的财务顾问和消费行为分析师，擅长分析消费数据，识别消费模式，并提供实用的财务建议。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            request_timeout=None,  # 不设置超时
        )

        print("AI分析生成成功!")
        ai_analysis = response.choices[0].message.content

        # 将AI回复分割为消费习惯分析和财务改善建议两部分
        analysis_parts = {}

        # 尝试分割AI回复
        if "财务改善建议" in ai_analysis:
            parts = ai_analysis.split("财务改善建议", 1)
            analysis_parts["habits_analysis"] = parts[0].strip()
            analysis_parts["financial_advice"] = "财务改善建议" + parts[1].strip()
        else:
            # 如果无法按预期分割，直接使用全文
            analysis_parts["habits_analysis"] = ai_analysis
            analysis_parts["financial_advice"] = ""

        print("AI分析结果处理完成")
        print("***** AI消费分析生成完成 *****\n")

        return {"ai_analysis": analysis_parts, "raw_response": ai_analysis}

    except Exception as e:
        print(f"***** 生成AI消费分析时发生错误 *****")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"错误堆栈:\n{traceback.format_exc()}")
        print("***** 错误信息结束 *****\n")

        return {
            "ai_analysis": {
                "habits_analysis": "很抱歉，分析生成过程中遇到了错误。",
                "financial_advice": "请稍后再试。",
            },
            "error": str(e),
        }


def analyze_spending_habits(
    user_id: int,
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> Dict[str, Any]:
    """分析用户的消费习惯"""
    analyzer = SpendingHabitsAnalyzer(user_id, db)

    # 1. 收集用户消费数据
    spending_data = {
        "basic_stats": analyzer.get_basic_stats(start_date, end_date),
        "spending_by_day": analyzer.get_spending_pattern_by_day(start_date, end_date),
        "favorite_categories": analyzer.get_favorite_categories(
            5, start_date, end_date
        ),
        "monthly_trend": analyzer.get_monthly_spending_trend(6, start_date, end_date),
        "recent_transactions": analyzer.get_recent_transactions(
            10, start_date, end_date
        ),
    }

    # 2. 使用AI生成消费习惯分析和建议
    ai_result = generate_ai_analysis(spending_data)

    # 3. 返回原始数据和AI分析结果
    return {
        "data": spending_data,
        "ai_analysis": ai_result["ai_analysis"],
    }
