from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc, case, distinct
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime, date, timedelta

from ..models.database import get_db
from ..models.models import Transaction, User, TransactionType
from .users import get_current_user
from ..services.spending_habits import analyze_spending_habits

router = APIRouter()


class ReportDateRange(BaseModel):
    start_date: date
    end_date: date


class TotalSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    start_date: date
    end_date: date
    transaction_stats: Optional[Dict[str, Any]] = None


class DailyRecord(BaseModel):
    date: date
    total_income: float
    total_expense: float
    balance: float


class CategorySummary(BaseModel):
    category: str
    total_amount: float
    percentage: float
    count: int = 0  # 设置默认值为0


class DetailedTransaction(BaseModel):
    id: int
    date: date
    description: str
    category: str
    amount: float
    transaction_type: str


class TransactionItem(BaseModel):
    id: int
    date: date
    description: str
    category: str
    amount: float
    transaction_type: str


class LargeTransactionsResponse(BaseModel):
    transactions: List[TransactionItem]
    start_date: date
    end_date: date


# 获取总收支概览
@router.get("/summary", response_model=TotalSummary)
def get_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_stats: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 如果未指定日期，默认查询当月数据
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    if not end_date:
        today = date.today()
        # 获取下个月的第一天，然后减去一天得到当月最后一天
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 确保参数是date类型而不是datetime类型
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    # 修复日期范围查询
    print(f"[Summary] Using date range: {start_date} to {end_date}")

    # 创建下一天日期，用于查询条件
    next_day = end_date + timedelta(days=1)
    print(
        f"[Summary] Using < {next_day} instead of <= {end_date} for end date condition"
    )

    # 查询总收入
    total_income = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.INCOME,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date
            < next_day,  # 使用 < next_day 而不是 <= end_date
        )
        .scalar()
        or 0.0
    )

    # 查询总支出
    total_expense = (
        db.query(func.sum(Transaction.amount))
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == TransactionType.EXPENSE,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date
            < next_day,  # 使用 < next_day 而不是 <= end_date
        )
        .scalar()
        or 0.0
    )

    # 计算结余
    balance = total_income - total_expense

    # 获取交易统计信息
    transaction_stats = None
    if include_stats:
        print("[Summary] Including transaction statistics")

        # 查询交易总笔数
        total_count = (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < next_day,
            )
            .scalar()
            or 0
        )

        # 查询收入交易笔数和总金额
        income_query = (
            db.query(
                func.count(Transaction.id).label("count"),
                func.sum(Transaction.amount).label("sum"),
            )
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.INCOME,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < next_day,
            )
            .first()
        )

        income_count = income_query.count or 0
        income_sum = income_query.sum or 0

        # 查询支出交易笔数和总金额
        expense_query = (
            db.query(
                func.count(Transaction.id).label("count"),
                func.sum(Transaction.amount).label("sum"),
            )
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == TransactionType.EXPENSE,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date < next_day,
            )
            .first()
        )

        expense_count = expense_query.count or 0
        expense_sum = expense_query.sum or 0

        # 计算平均每笔金额
        avg_income = income_sum / income_count if income_count > 0 else 0
        avg_expense = expense_sum / expense_count if expense_count > 0 else 0

        # 计算日均交易笔数
        days_count = (end_date - start_date).days + 1
        daily_avg = total_count / days_count if days_count > 0 else 0

        transaction_stats = {
            "total_count": total_count,
            "income_count": income_count,
            "expense_count": expense_count,
            "avg_income": avg_income,
            "avg_expense": avg_expense,
            "daily_avg": round(daily_avg, 1),
        }

    return TotalSummary(
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        start_date=start_date,
        end_date=end_date,
        transaction_stats=transaction_stats,
    )


# 获取每日收支趋势
@router.get("/daily", response_model=List[DailyRecord])
def get_daily_trend(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # 如果未指定日期，默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)  # 30天包含今天

        # 确保参数是date类型而不是datetime类型
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        # 修复日期范围查询
        print(f"[Daily Trend] Using date range: {start_date} to {end_date}")

        # 创建下一天日期，用于查询条件
        next_day = end_date + timedelta(days=1)
        print(
            f"[Daily Trend] Using < {next_day} instead of <= {end_date} for end date condition"
        )

        # 生成日期序列
        date_range = []
        delta = end_date - start_date
        for i in range(delta.days + 1):
            date_range.append(start_date + timedelta(days=i))

        # 查询每日收入和支出
        daily_transactions = (
            db.query(
                Transaction.transaction_date,
                Transaction.type,
                func.sum(Transaction.amount).label("total_amount"),
            )
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date
                < next_day,  # 使用 < next_day 而不是 <= end_date
            )
            .group_by(Transaction.transaction_date, Transaction.type)
            .all()
        )

        # 整理数据
        results = {}
        for date_item in date_range:
            # 确保使用date类型作为字典键
            date_key = (
                date_item.date() if isinstance(date_item, datetime) else date_item
            )
            results[date_key] = {
                "total_income": 0.0,
                "total_expense": 0.0,
                "balance": 0.0,
            }

        for record in daily_transactions:
            # 确保使用date类型作为字典键
            transaction_date = (
                record.transaction_date.date()
                if isinstance(record.transaction_date, datetime)
                else record.transaction_date
            )
            amount = record.total_amount or 0.0

            # 确保键存在
            if transaction_date not in results:
                # 如果数据库中有不在日期范围内的记录，跳过
                continue

            if record.type == TransactionType.INCOME:
                results[transaction_date]["total_income"] = amount
            else:  # EXPENSE
                results[transaction_date]["total_expense"] = amount

            results[transaction_date]["balance"] = (
                results[transaction_date]["total_income"]
                - results[transaction_date]["total_expense"]
            )

        # 转换为响应格式并按日期排序
        response = []
        for day, data in sorted(results.items()):
            response.append(
                DailyRecord(
                    date=day,
                    total_income=data["total_income"],
                    total_expense=data["total_expense"],
                    balance=data["balance"],
                )
            )

        return response
    except Exception as e:
        # 记录错误并返回友好错误信息
        print(f"Error in get_daily_trend: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理每日趋势数据时出错: {str(e)}",
        )


# 获取分类排行
@router.get("/category-ranking", response_model=List[CategorySummary])
def get_category_ranking(
    transaction_type: TransactionType,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 如果未指定日期，默认查询当月数据
    if not start_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
    if not end_date:
        today = date.today()
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # 确保参数是date类型而不是datetime类型
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    # 修复日期范围查询
    print(f"[Category Ranking] Using date range: {start_date} to {end_date}")

    # 创建下一天日期，用于查询条件
    next_day = end_date + timedelta(days=1)
    print(
        f"[Category Ranking] Using < {next_day} instead of <= {end_date} for end date condition"
    )

    try:
        # 查询所有满足条件的交易记录总金额
        total_amount_query = db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == transaction_type,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date
            < next_day,  # 使用 < next_day 而不是 <= end_date
        )
        total_amount = total_amount_query.scalar() or 0

        # 查询每个类别的总金额和记录数量
        category_stats = (
            db.query(
                Transaction.category,
                func.sum(Transaction.amount).label("total_amount"),
                func.count(Transaction.id).label("count"),
            )
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == transaction_type,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date
                < next_day,  # 使用 < next_day 而不是 <= end_date
            )
            .group_by(Transaction.category)
            .order_by(desc("total_amount"))
            .all()
        )

        # 准备返回数据，计算百分比
        result = []
        for item in category_stats:
            category = item.category or "未分类"
            amount = float(item.total_amount)
            count = item.count
            percentage = (
                round((amount / total_amount * 100), 2) if total_amount > 0 else 0
            )

            result.append(
                CategorySummary(
                    category=category,
                    total_amount=amount,
                    percentage=percentage,
                    count=count,
                )
            )

        return result
    except Exception as e:
        print(f"Error in get_category_ranking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理分类排行数据时出错: {str(e)}",
        )


# 获取明细排行
@router.get("/transaction-ranking", response_model=List[DetailedTransaction])
def get_transaction_ranking(
    transaction_type: TransactionType,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 20,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # 如果未指定日期，默认查询当月数据
        if not start_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
        if not end_date:
            today = date.today()
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # 确保参数是date类型而不是datetime类型
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        # 修复日期范围查询
        print(f"[Transaction Ranking] Using date range: {start_date} to {end_date}")

        # 创建下一天日期，用于查询条件
        next_day = end_date + timedelta(days=1)
        print(
            f"[Transaction Ranking] Using < {next_day} instead of <= {end_date} for end date condition"
        )

        # 查询交易记录，按金额降序排列
        transactions = (
            db.query(
                Transaction.id,
                Transaction.transaction_date,
                Transaction.description,
                Transaction.category,
                Transaction.amount,
                Transaction.type,
            )
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == transaction_type,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date
                < next_day,  # 使用 < next_day 而不是 <= end_date
            )
            .order_by(desc(Transaction.amount))
            .limit(limit)
            .all()
        )

        # 记录找到的交易记录及其日期
        print(f"[Transaction Ranking] Found {len(transactions)} transactions")
        for tx in transactions:
            print(
                f"[Transaction Ranking] Transaction date: {tx.transaction_date}, amount: {tx.amount}"
            )

        # 整理数据
        result = []
        for tx in transactions:
            # 确保日期是date类型
            tx_date = tx.transaction_date
            if isinstance(tx_date, datetime):
                tx_date = tx_date.date()

            result.append(
                DetailedTransaction(
                    id=tx.id,
                    date=tx_date,
                    description=tx.description or "",
                    category=tx.category or "未分类",
                    amount=tx.amount,
                    transaction_type=tx.type,
                )
            )

        return result
    except Exception as e:
        # 记录错误并返回友好错误信息
        print(f"Error in get_transaction_ranking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理明细排行数据时出错: {str(e)}",
        )


# 获取总账单（按天排序显示收入、支出和结余）
@router.get("/ledger")
def get_ledger(
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    transaction_type: Optional[str] = None,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        print(
            f"Ledger API called with params: start_date={start_date}, end_date={end_date}, transaction_type={transaction_type}, category={category}, keyword={keyword}"
        )
        today = date.today()

        # 处理日期范围参数
        if start_date and end_date:
            # 如果提供了日期范围，优先使用日期范围
            # 确保参数是date类型而不是datetime类型
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()
            print(f"Using provided date range: {start_date} to {end_date}")
        else:
            # 如果未指定日期范围，使用年月日参数
            # 如果未指定年份，使用当前年份
            if not year:
                year = today.year
                print(f"No year provided, using current year: {year}")

            # 构建查询的开始和结束日期
            if month:
                if day:
                    # 如果指定了具体日期
                    try:
                        query_date = date(year, month, day)
                        start_date = query_date
                        end_date = query_date
                        print(f"Using specific date: {query_date}")
                    except ValueError as e:
                        print(
                            f"Invalid date: year={year}, month={month}, day={day}, error: {str(e)}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"无效的日期: {str(e)}",
                        )
                else:
                    # 如果只指定了月份
                    try:
                        start_date = date(year, month, 1)
                        # 计算月末
                        if month == 12:
                            end_date = date(year + 1, 1, 1) - timedelta(days=1)
                        else:
                            end_date = date(year, month + 1, 1) - timedelta(days=1)
                        print(f"Using month range: {start_date} to {end_date}")
                    except ValueError as e:
                        print(
                            f"Invalid month: year={year}, month={month}, error: {str(e)}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"无效的月份: {str(e)}",
                        )
            else:
                # 如果只指定了年份
                try:
                    start_date = date(year, 1, 1)
                    end_date = date(year, 12, 31)
                    print(f"Using year range: {start_date} to {end_date}")
                except ValueError as e:
                    print(f"Invalid year: {year}, error: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"无效的年份: {str(e)}",
                    )

        # 构建基本查询
        try:
            # 确保参数是date类型而不是datetime类型
            if isinstance(start_date, datetime):
                start_date = start_date.date()
            if isinstance(end_date, datetime):
                end_date = end_date.date()

            # 修复日期范围查询
            print(f"[Ledger] Using date range: {start_date} to {end_date}")

            # 创建下一天日期，用于查询条件
            next_day = end_date + timedelta(days=1)
            print(
                f"[Ledger] Using < {next_day} instead of <= {end_date} for end date condition"
            )

            # 查询所有交易记录
            transactions_query = db.query(
                Transaction.id,
                Transaction.transaction_date,
                Transaction.description,
                Transaction.category,
                Transaction.amount,
                Transaction.type,
            ).filter(
                Transaction.user_id == current_user.id,
                Transaction.is_deleted == False,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date
                < next_day,  # 使用 < next_day 而不是 <= end_date
            )

            # 应用额外的过滤条件
            if transaction_type:
                if transaction_type.lower() != "all":
                    transactions_query = transactions_query.filter(
                        Transaction.type == transaction_type
                    )
                    print(f"Filtering by transaction_type: {transaction_type}")

            if category:
                transactions_query = transactions_query.filter(
                    Transaction.category == category
                )
                print(f"Filtering by category: {category}")

            if keyword:
                transactions_query = transactions_query.filter(
                    Transaction.description.ilike(f"%{keyword}%")
                )
                print(f"Filtering by keyword: {keyword}")

            # 获取所有交易记录
            all_transactions = transactions_query.all()
            print(f"Retrieved {len(all_transactions)} total transactions")

            # 按日期分组统计
            daily_stats = {}
            for tx in all_transactions:
                # 确保日期是date类型
                tx_date = tx.transaction_date
                if isinstance(tx_date, datetime):
                    tx_date = tx_date.date()

                # 将日期转换为字符串键
                date_key = tx_date.isoformat()

                # 初始化该日期的统计数据
                if date_key not in daily_stats:
                    daily_stats[date_key] = {
                        "date": date_key,
                        "total_income": 0.0,
                        "total_expense": 0.0,
                        "balance": 0.0,
                        "transactions": [],
                    }

                # 添加交易记录
                tx_data = {
                    "id": tx.id,
                    "date": date_key,
                    "description": tx.description or "",
                    "category": tx.category or "未分类",
                    "amount": float(tx.amount),
                    "type": tx.type,
                    "transaction_type": tx.type,
                }

                # 更新统计数据
                if tx.type == TransactionType.INCOME:
                    daily_stats[date_key]["total_income"] += tx.amount
                else:
                    daily_stats[date_key]["total_expense"] += tx.amount

                daily_stats[date_key]["transactions"].append(tx_data)

            # 计算每日结余
            for date_key in daily_stats:
                daily_stats[date_key]["balance"] = (
                    daily_stats[date_key]["total_income"]
                    - daily_stats[date_key]["total_expense"]
                )

            # 转换为列表并按日期降序排序
            daily_records = list(daily_stats.values())
            daily_records.sort(key=lambda x: x["date"], reverse=True)

            # 计算总计
            total_income = sum(day["total_income"] for day in daily_records)
            total_expense = sum(day["total_expense"] for day in daily_records)
            total_balance = total_income - total_expense

            # 应用分页
            total_count = len(daily_records)
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_count)
            paged_records = daily_records[start_idx:end_idx]

            # 构建响应
            result = {
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size,
                "start_date": (
                    start_date.isoformat()
                    if hasattr(start_date, "isoformat")
                    else str(start_date)
                ),
                "end_date": (
                    end_date.isoformat()
                    if hasattr(end_date, "isoformat")
                    else str(end_date)
                ),
                "total_income": total_income,
                "total_expense": total_expense,
                "total_balance": total_balance,
                "daily_records": paged_records,
            }

            print(
                f"API response prepared: {len(paged_records)} daily records, total income: {total_income}, total expense: {total_expense}"
            )

            return result
        except Exception as e:
            print(f"Error in database query: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询数据库时出错: {str(e)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        # 记录错误并返回友好错误信息
        print(f"Unexpected error in get_ledger: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理总账单数据时出错: {str(e)}",
        )


# 获取用户消费习惯分析
@router.get("/spending-habits")
def get_spending_habits(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """分析用户消费习惯"""
    try:
        # 调用消费习惯分析服务
        habits_analysis = analyze_spending_habits(
            current_user.id, db, start_date, end_date
        )
        return habits_analysis
    except Exception as e:
        # 记录错误并返回友好错误信息
        print(f"Error in get_spending_habits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分析消费习惯时出错: {str(e)}",
        )


# 获取大额交易
@router.get("/large-transactions", response_model=LargeTransactionsResponse)
def get_large_transactions(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 5,
    sort_by: str = "amount",
    sort_order: str = "abs_desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定日期范围内的大额交易记录，按金额排序
    - sort_order: "desc" 降序, "asc" 升序, "abs_desc" 按绝对值降序
    """
    try:
        # 如果未指定日期，默认查询最近30天
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=29)  # 30天包含今天

        # 确保参数是date类型而不是datetime类型
        if isinstance(start_date, datetime):
            start_date = start_date.date()
        if isinstance(end_date, datetime):
            end_date = end_date.date()

        print(f"[Large Transactions] Using date range: {start_date} to {end_date}")

        # 创建下一天日期，用于查询条件
        next_day = end_date + timedelta(days=1)
        print(
            f"[Large Transactions] Using < {next_day} instead of <= {end_date} for end date condition"
        )

        # 构建基本查询
        transactions_query = db.query(
            Transaction.id,
            Transaction.transaction_date,
            Transaction.description,
            Transaction.category,
            Transaction.amount,
            Transaction.type,
        ).filter(
            Transaction.user_id == current_user.id,
            Transaction.is_deleted == False,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date < next_day,
        )

        # 应用排序
        if sort_order == "abs_desc":
            # 按金额绝对值降序排序（不区分收入和支出）
            transactions_query = transactions_query.order_by(
                desc(func.abs(Transaction.amount))
            )
        elif sort_order == "desc":
            # 按金额降序排序
            transactions_query = transactions_query.order_by(desc(Transaction.amount))
        else:
            # 按金额升序排序
            transactions_query = transactions_query.order_by(Transaction.amount)

        # 限制返回记录数
        transactions = transactions_query.limit(limit).all()

        # 转换为响应格式
        result = []
        for tx in transactions:
            # 确保日期是date类型
            tx_date = tx.transaction_date
            if isinstance(tx_date, datetime):
                tx_date = tx_date.date()

            result.append(
                TransactionItem(
                    id=tx.id,
                    date=tx_date,
                    description=tx.description or "",
                    category=tx.category or "未分类",
                    amount=float(tx.amount),
                    transaction_type=tx.type,
                )
            )

        return LargeTransactionsResponse(
            transactions=result,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        print(f"Error in get_large_transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取大额交易数据时出错: {str(e)}",
        )
