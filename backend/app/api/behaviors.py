# =============================================================================
# 智能零售用户行为分析系统 - 行为数据模块 API 路由
# =============================================================================
# 4个接口:
#   6.1 POST /behaviors/import  - 批量导入行为数据（Excel/CSV）
#   6.2 GET  /behaviors          - 分页查询行为记录（多条件筛选）
#   6.3 GET  /behaviors/funnel  - 获取行为转化漏斗
#   6.4 GET  /behaviors/trend   - 获取用户行为趋势（PV/UV）
# =============================================================================

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, distinct
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd
import io

from app.schemas.behavior import BehaviorItem, ImportResult, FunnelStep, FunnelData, TrendData
from app.models.behavior import Behavior
from app.models.base import get_db
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.jwt_utils import get_current_user


router = APIRouter(prefix="/behaviors", tags=["行为数据"])


# ======================== 6.1 导入行为数据 ========================

@router.post("/import", summary="导入行为数据")
async def import_behaviors(
    file: UploadFile = File(..., description="Excel/CSV文件"),
    mode: str = Form(default="append", description="导入模式: append=追加, replace=替换"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    批量导入用户行为数据
    
    支持 Excel(.xlsx/.xls) 和 CSV(.csv) 格式
    文件需包含列: user_id, product_id, behavior_type
    mode=replace 时先清空已有数据再导入
    """
    # 校验文件格式
    filename = file.filename or ""
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="仅支持 .csv/.xlsx/.xls 格式文件")
    
    try:
        contents = await file.read()
        # 根据扩展名解析文件
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="文件解析失败，请检查文件格式")
    
    # 校验必要列
    required = ["user_id", "product_id", "behavior_type"]
    for col in required:
        if col not in df.columns:
            return error_response(code=status.HTTP_400_BAD_REQUEST, message=f"缺少必要列: {col}")
    
    # 校验 behavior_type 取值
    valid_types = {"view", "cart", "favorite", "buy"}
    df["behavior_type"] = df["behavior_type"].astype(str).str.strip().str.lower()
    invalid = df[~df["behavior_type"].isin(valid_types)]
    if len(invalid) > 0:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message=f"包含无效行为类型: {invalid['behavior_type'].unique().tolist()}")
    
    # replace模式: 清空已有数据
    if mode == "replace":
        db.query(Behavior).delete()
        db.commit()
    
    # 批量插入
    imported, skipped = 0, 0
    for _, row in df.iterrows():
        try:
            b = Behavior(
                user_id=int(row["user_id"]),
                product_id=int(row["product_id"]),
                behavior_type=row["behavior_type"]
            )
            db.add(b)
            imported += 1
        except Exception:
            skipped += 1
    
    db.commit()
    
    return success_response(
        data=ImportResult(imported_count=imported, skipped_count=skipped).model_dump(),
        message="导入成功"
    )


# ======================== 6.2 获取行为数据列表 ========================

@router.get("", summary="获取行为数据列表")
async def get_behaviors(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(default=None, description="用户ID"),
    product_id: Optional[int] = Query(default=None, description="商品ID"),
    behavior_type: Optional[str] = Query(default=None, description="行为类型: view/cart/favorite/buy"),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """分页查询行为记录，支持多条件筛选"""
    query = db.query(Behavior)
    
    if user_id:
        query = query.filter(Behavior.user_id == user_id)
    if product_id:
        query = query.filter(Behavior.product_id == product_id)
    if behavior_type:
        query = query.filter(Behavior.behavior_type == behavior_type)
    if start_date:
        query = query.filter(Behavior.created_at >= start_date)
    if end_date:
        query = query.filter(Behavior.created_at <= end_date + " 23:59:59")
    
    total = query.count()
    records = query.order_by(Behavior.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    items = [
        BehaviorItem(
            id=r.id, user_id=r.user_id, product_id=r.product_id,
            behavior_type=str(r.behavior_type), created_at=r.created_at
        ).model_dump() for r in records
    ]
    return paginated_response(items=items, total=total, page=page, page_size=page_size)


# ======================== 6.3 获取行为转化漏斗 ========================

@router.get("/funnel", summary="获取行为转化漏斗")
async def get_behavior_funnel(
    start_date: Optional[str] = Query(default=None, description="开始日期"),
    end_date: Optional[str] = Query(default=None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取用户行为转化漏斗
    
    漏斗顺序: 浏览(view) → 加购(cart) → 购买(buy)
    每个步骤统计去重用户数，rate 以第一步为基准(1.0)
    """
    base_query = db.query(Behavior)
    if start_date:
        base_query = base_query.filter(Behavior.created_at >= start_date)
    if end_date:
        base_query = base_query.filter(Behavior.created_at <= end_date + " 23:59:59")
    
    # 统计每种行为的去重用户数（使用 func.count + func.distinct 确保正确去重）
    view_users = db.query(sqlfunc.count(sqlfunc.distinct(Behavior.user_id))).filter(
        Behavior.behavior_type == "view", *([Behavior.created_at >= start_date] if start_date else []),
        *([Behavior.created_at <= end_date + " 23:59:59"] if end_date else [])
    ).scalar() or 0
    cart_users = db.query(sqlfunc.count(sqlfunc.distinct(Behavior.user_id))).filter(
        Behavior.behavior_type == "cart", *([Behavior.created_at >= start_date] if start_date else []),
        *([Behavior.created_at <= end_date + " 23:59:59"] if end_date else [])
    ).scalar() or 0
    buy_users = db.query(sqlfunc.count(sqlfunc.distinct(Behavior.user_id))).filter(
        Behavior.behavior_type == "buy", *([Behavior.created_at >= start_date] if start_date else []),
        *([Behavior.created_at <= end_date + " 23:59:59"] if end_date else [])
    ).scalar() or 0
    
    base = max(view_users, 1)  # 避免除零
    steps = [
        FunnelStep(name="浏览", count=view_users, rate=round(view_users / base, 2)),
        FunnelStep(name="加购", count=cart_users, rate=round(cart_users / base, 2)),
        FunnelStep(name="购买", count=buy_users, rate=round(buy_users / base, 2)),
    ]
    return success_response(data=FunnelData(steps=steps).model_dump())


# ======================== 6.4 获取行为趋势 ========================

@router.get("/trend", summary="获取行为趋势")
async def get_behavior_trend(
    days: int = Query(default=30, ge=1, le=365, description="查询天数"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取用户行为趋势数据（PV/UV/各行为类型数量）
    
    返回每日: PV(总行为数), UV(去重用户数), view_count, cart_count, buy_count
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    records = db.query(Behavior).filter(Behavior.created_at >= start_date).order_by(Behavior.created_at.asc()).all()
    
    # 按天聚合
    from collections import defaultdict
    daily = defaultdict(lambda: {"pv": 0, "users": set(), "view": 0, "cart": 0, "buy": 0})
    for r in records:
        key = r.created_at.strftime("%Y-%m-%d")
        daily[key]["pv"] += 1
        daily[key]["users"].add(r.user_id)
        bt = str(r.behavior_type)
        if bt in daily[key]:
            daily[key][bt] += 1
    
    dates, pv, uv, vc, cc, bc = [], [], [], [], [], []
    for i in range(days, -1, -1):
        d = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)
        pv.append(daily[d]["pv"])
        uv.append(len(daily[d]["users"]))
        vc.append(daily[d]["view"])
        cc.append(daily[d]["cart"])
        bc.append(daily[d]["buy"])
    
    return success_response(data=TrendData(
        dates=dates, pv=pv, uv=uv, view_count=vc, cart_count=cc, buy_count=bc
    ).model_dump())
