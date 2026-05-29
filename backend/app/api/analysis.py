# =============================================================================
# 智能零售用户行为分析系统 - 数据分析模块 API 路由
# =============================================================================
# 5个接口:
#   7.1 GET  /analysis/rfm          - RFM用户价值分析
#   7.2 GET  /analysis/cluster      - K-Means用户分群
#   7.3 POST /analysis/recalculate  - 触发重新计算
#   7.4 GET  /analysis/association  - Apriori关联规则
#   7.5 GET  /analysis/profile/{id} - 用户画像
# =============================================================================

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional

from app.schemas.analysis import (
    RecalculateRequest, RFMResult, RFMDistribution, RFMScoreItem,
    ClusterResultResponse, ClusterItem, ClusterPoint,
    AssociationResult, AssociationRule,
    UserProfileResponse, PreferCategory
)
from app.models.rfm_score import RfmScore
from app.models.cluster_result import ClusterResult
from app.models.base import get_db
from app.utils.response_utils import success_response, error_response
from app.utils.jwt_utils import get_current_user
from app.services.analysis_service import calculate_rfm, calculate_cluster, calculate_association, get_user_profile


router = APIRouter(prefix="/analysis", tags=["数据分析"])


# ======================== 7.1 RFM 用户价值分析 ========================

@router.get("/rfm", summary="RFM用户价值分析")
async def get_rfm(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取RFM分析结果
    
    如果数据库中没有RFM数据，自动触发计算并存储
    """
    scores = db.query(RfmScore).all()
    if not scores:
        # 没有数据，自动计算
        result = calculate_rfm(db)
    else:
        # 已有数据，直接读取
        segments_count = {}
        score_list = []
        for s in scores:
            seg = s.segment or "流失用户"
            segments_count[seg] = segments_count.get(seg, 0) + 1
            score_list.append(RFMScoreItem(
                user_id=s.user_id, recency=s.recency or 1, frequency=s.frequency or 1,
                monetary=s.monetary or 1, segment=seg
            ).model_dump())
        labels = ["高价值用户", "忠诚用户", "潜力用户", "流失用户"]
        result = {
            "distribution": {"labels": labels, "values": [segments_count.get(l, 0) for l in labels]},
            "scores": score_list
        }
    
    return success_response(data=RFMResult(
        distribution=RFMDistribution(**result["distribution"]),
        scores=[RFMScoreItem(**s) for s in result["scores"]]
    ).model_dump())


# ======================== 7.2 K-Means 用户分群 ========================

@router.get("/cluster", summary="K-Means用户分群")
async def get_cluster(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取K-Means聚类结果（散点图/雷达图数据）"""
    records = db.query(ClusterResult).all()
    if not records:
        # 确保RFM存在
        if not db.query(RfmScore).count():
            calculate_rfm(db)
        result = calculate_cluster(db)
        records = db.query(ClusterResult).all()
    else:
        # 构建聚类结果
        from collections import defaultdict
        rfm_map = {s.user_id: s for s in db.query(RfmScore).all()}
        groups = defaultdict(list)
        for c in records:
            rfm = rfm_map.get(c.user_id)
            groups[c.cluster_label].append({
                "user_id": c.user_id,
                "x": float(rfm.recency) if rfm else 0,
                "y": float(rfm.frequency) if rfm else 0,
                "z": float(rfm.monetary) if rfm else 0
            })
        cls_names = ["高消费活跃用户", "中等消费用户", "潜力用户", "低频用户", "流失用户"]
        clusters = []
        for label, pts in sorted(groups.items()):
            cx = sum(p["x"] for p in pts) / len(pts) if pts else 0
            cy = sum(p["y"] for p in pts) / len(pts) if pts else 0
            cz = sum(p["z"] for p in pts) / len(pts) if pts else 0
            clusters.append({"label": label, "name": cls_names[label] if label < len(cls_names) else f"群{label}",
                           "count": len(pts), "center": [round(cx, 1), round(cy, 1), round(cz, 1)], "points": pts})
        result = {"clusters": clusters}
    
    resp = ClusterResultResponse(clusters=[
        ClusterItem(label=c["label"], name=c["name"], count=c["count"],
                    center=c["center"], points=[ClusterPoint(**p) for p in c["points"]])
        for c in result["clusters"]
    ])
    return success_response(data=resp.model_dump())


# ======================== 7.3 触发重新计算 ========================

@router.post("/recalculate", summary="触发重新计算")
async def recalculate_analysis(
    request: RecalculateRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """触发后台重新计算RFM和/或聚类结果"""
    results = {}
    if request.type in ("rfm", "all"):
        calc_rfm = calculate_rfm(db)
        results["rfm"] = {"segments": calc_rfm["distribution"]["values"]}
    if request.type in ("cluster", "all"):
        calc_cluster = calculate_cluster(db, request.clusters)
        results["cluster"] = {"groups": len(calc_cluster.get("clusters", []))}
    if request.type not in ("rfm", "cluster", "all"):
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="type必须为 rfm/cluster/all")
    
    return success_response(data=results, message="重新计算完成")


# ======================== 7.4 关联规则挖掘 ========================

@router.get("/association", summary="关联规则挖掘")
async def get_association(
    min_support: float = Query(default=0.01, ge=0.001, le=1.0, description="最小支持度"),
    min_confidence: float = Query(default=0.5, ge=0.1, le=1.0, description="最小置信度"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取商品关联规则（Apriori算法）
    
    基于订单数据中的商品共现关系，挖掘关联规则
    返回规则包含支持度(support)、置信度(confidence)、提升度(lift)
    """
    rules = calculate_association(db, min_support, min_confidence, limit)
    resp = AssociationResult(rules=[
        AssociationRule(**r) for r in rules
    ])
    return success_response(data=resp.model_dump())


# ======================== 7.5 用户画像 ========================

@router.get("/profile/{user_id}", summary="用户画像")
async def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取指定用户的画像数据（偏好分类、活跃时段、标签等）"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return error_response(code=status.HTTP_404_NOT_FOUND, message="用户不存在")
    
    resp = UserProfileResponse(
        user_id=profile["user_id"], nickname=profile["nickname"],
        tags=profile["tags"],
        prefer_categories=[PreferCategory(**c) for c in profile["prefer_categories"]],
        active_hours=profile["active_hours"],
        avg_order_value=profile["avg_order_value"],
        total_orders=profile["total_orders"],
        days_since_last_purchase=profile["days_since_last_purchase"]
    )
    return success_response(data=resp.model_dump())
