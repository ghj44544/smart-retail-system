from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.behavior import Behavior
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.rfm_score import RfmScore
from app.models.user import User
from app.services.analysis_service import calculate_association, calculate_rfm


COMPLETED_STATUSES = ("completed", "paid", "shipped")

KNOWLEDGE_BASE = [
    {
        "id": "rfm",
        "title": "RFM 用户分层",
        "keywords": ["rfm", "用户分层", "高价值", "忠诚", "流失"],
        "summary": "RFM 用最近购买、购买频次、消费金额识别高价值用户、忠诚用户、潜力用户和流失用户。",
        "suggestions": [
            "高价值用户适合会员权益、专属优惠和新品优先触达。",
            "潜力用户适合首单后复购券、组合推荐和加购提醒。",
            "流失用户适合限时召回、价格敏感型优惠和低频触达。",
        ],
    },
    {
        "id": "association",
        "title": "商品关联规则",
        "keywords": ["关联", "搭配", "连带", "组合", "推荐"],
        "summary": "关联规则通过支持度、置信度、提升度发现常被一起购买的商品组合。",
        "suggestions": [
            "高提升度规则适合做购物车搭配推荐。",
            "高置信度规则适合做详情页加购提示。",
            "组合商品需要关注库存，避免推荐缺货商品。",
        ],
    },
    {
        "id": "conversion",
        "title": "行为转化分析",
        "keywords": ["转化", "漏斗", "浏览", "加购", "购买"],
        "summary": "浏览、加购、收藏、购买的比例可以定位用户在哪一步流失。",
        "suggestions": [
            "浏览高但加购低时，优先检查价格、主图、评价和卖点表达。",
            "加购高但购买低时，优先优化优惠、运费、库存和结算流程。",
            "收藏高的商品适合做降价提醒和限时活动。",
        ],
    },
    {
        "id": "inventory",
        "title": "库存与热销风险",
        "keywords": ["库存", "热销", "缺货", "补货"],
        "summary": "热销且库存偏低的商品需要优先补货，低销量高库存商品需要促销或下架评估。",
        "suggestions": [
            "按销量/库存比识别补货优先级。",
            "低销量高库存商品可尝试捆绑销售、折扣清仓或曝光调整。",
            "库存策略应结合关联规则，保证组合推荐中的主商品和配件都有货。",
        ],
    },
]


def _safe_float(value) -> float:
    return float(value or 0)


def _completed_orders(db: Session):
    return db.query(Order).filter(Order.status.in_(COMPLETED_STATUSES))


def get_ai_summary(db: Session) -> Dict:
    total_users = db.query(User).filter(User.deleted_at == None).count()
    total_products = db.query(Product).filter(Product.deleted_at == None).count()
    active_products = db.query(Product).filter(Product.deleted_at == None, Product.status == "on").count()
    completed_orders = _completed_orders(db)

    total_orders = completed_orders.count()
    total_sales = _safe_float(completed_orders.with_entities(func.coalesce(func.sum(Order.total_amount), 0)).scalar())
    avg_order_value = round(total_sales / total_orders, 2) if total_orders else 0

    since_30d = datetime.utcnow() - timedelta(days=30)
    recent_sales = _safe_float(
        completed_orders.filter(Order.created_at >= since_30d)
        .with_entities(func.coalesce(func.sum(Order.total_amount), 0))
        .scalar()
    )
    recent_orders = completed_orders.filter(Order.created_at >= since_30d).count()

    behavior_counts = dict(
        db.query(Behavior.behavior_type, func.count(Behavior.id))
        .group_by(Behavior.behavior_type)
        .all()
    )
    views = int(behavior_counts.get("view", 0))
    carts = int(behavior_counts.get("cart", 0))
    buys = int(behavior_counts.get("buy", 0))
    cart_rate = round(min(carts / views, 1) * 100, 2) if views else 0
    buy_rate = round(min(buys / views, 1) * 100, 2) if views else 0

    if not db.query(RfmScore).count() and total_users:
        try:
            calculate_rfm(db)
        except Exception:
            db.rollback()

    rfm_rows = db.query(RfmScore.segment, func.count(RfmScore.user_id)).group_by(RfmScore.segment).all()
    segment_counts = {segment or "未分层": count for segment, count in rfm_rows}

    top_products = (
        db.query(
            Product.id,
            Product.name,
            Product.stock,
            Product.sales_count,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("sold_qty"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.price), 0).label("revenue"),
        )
        .outerjoin(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.deleted_at == None)
        .group_by(Product.id)
        .order_by(func.coalesce(func.sum(OrderItem.quantity * OrderItem.price), 0).desc())
        .limit(8)
        .all()
    )

    product_rank = [
        {
            "id": row.id,
            "name": row.name,
            "stock": int(row.stock or 0),
            "sales_count": int(row.sales_count or 0),
            "sold_qty": int(row.sold_qty or 0),
            "revenue": round(_safe_float(row.revenue), 2),
        }
        for row in top_products
    ]

    low_stock_hot = [p for p in product_rank if p["sold_qty"] >= 1 and p["stock"] <= max(5, p["sold_qty"] * 0.2)]

    insights: List[Dict] = []
    if total_sales:
        insights.append({
            "type": "sales",
            "title": "经营规模",
            "content": f"累计成交 {total_orders} 单，销售额 {total_sales:.2f} 元，客单价 {avg_order_value:.2f} 元。",
            "priority": "high",
        })
    else:
        insights.append({
            "type": "sales",
            "title": "数据准备",
            "content": "当前成交数据较少，建议先导入订单或运行演示数据，再使用 AI 经营分析。",
            "priority": "medium",
        })

    if views:
        insights.append({
            "type": "conversion",
            "title": "转化漏斗",
            "content": f"浏览到加购转化率 {cart_rate:.2f}%，浏览到购买转化率 {buy_rate:.2f}%。",
            "priority": "high" if buy_rate < 5 else "medium",
        })

    if segment_counts:
        main_segment, main_count = max(segment_counts.items(), key=lambda item: item[1])
        insights.append({
            "type": "user",
            "title": "用户结构",
            "content": f"当前占比最高的用户层级是「{main_segment}」，共 {main_count} 人。",
            "priority": "medium",
        })

    if low_stock_hot:
        names = "、".join(p["name"] for p in low_stock_hot[:3])
        insights.append({
            "type": "inventory",
            "title": "热销库存提醒",
            "content": f"{names} 等商品销量较活跃但库存偏低，建议优先检查补货。",
            "priority": "high",
        })

    return {
        "metrics": {
            "total_users": total_users,
            "total_products": total_products,
            "active_products": active_products,
            "total_orders": total_orders,
            "total_sales": round(total_sales, 2),
            "avg_order_value": avg_order_value,
            "recent_30d_orders": recent_orders,
            "recent_30d_sales": round(recent_sales, 2),
            "view_count": views,
            "cart_count": carts,
            "buy_count": buys,
            "cart_rate": cart_rate,
            "buy_rate": buy_rate,
        },
        "segments": segment_counts,
        "top_products": product_rank,
        "insights": insights,
    }


def search_knowledge(query: str = "") -> List[Dict]:
    normalized = (query or "").strip().lower()
    if not normalized:
        return KNOWLEDGE_BASE

    scored = []
    for item in KNOWLEDGE_BASE:
        text = " ".join([item["title"], item["summary"], *item["keywords"]]).lower()
        score = sum(1 for token in item["keywords"] if token.lower() in normalized)
        if normalized in text:
            score += 2
        if score:
            scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored] or KNOWLEDGE_BASE[:2]


def answer_question(db: Session, question: str) -> Dict:
    summary = get_ai_summary(db)
    q = (question or "").strip()
    lowered = q.lower()
    sources = ["经营指标", "用户分层", "商品与行为数据"]
    suggestions: List[str] = []

    if not q:
        answer = "你可以问我：最近经营情况怎么样、哪些商品值得补货、用户分层怎么做运营、如何提升转化率。"
        return {"answer": answer, "suggestions": [], "sources": sources, "related_knowledge": search_knowledge("")}

    if any(word in lowered for word in ["库存", "补货", "缺货", "stock"]):
        products = summary["top_products"][:5]
        if products:
            lines = [f"{p['name']}：库存 {p['stock']}，已售 {p['sold_qty']}，销售额 {p['revenue']:.2f} 元" for p in products]
            answer = "从热销商品看，建议优先检查这些商品的库存：\n" + "\n".join(lines)
        else:
            answer = "当前商品销售明细不足，暂时无法判断补货优先级。"
        suggestions = ["先保障热销商品库存", "低库存商品可暂停强推荐", "结合关联商品一起检查库存"]
    elif any(word in lowered for word in ["转化", "漏斗", "加购", "购买", "conversion"]):
        m = summary["metrics"]
        answer = (
            f"当前浏览 {m['view_count']} 次、加购 {m['cart_count']} 次、购买 {m['buy_count']} 次。"
            f"浏览到加购转化率 {m['cart_rate']:.2f}%，浏览到购买转化率 {m['buy_rate']:.2f}%。"
        )
        suggestions = ["浏览高加购低时优化价格和详情页卖点", "加购高购买低时检查优惠、运费和结算流程", "对收藏和加购用户做限时提醒"]
    elif any(word in lowered for word in ["rfm", "分层", "用户", "流失", "高价值"]):
        segments = summary["segments"]
        if segments:
            parts = [f"{name} {count} 人" for name, count in segments.items()]
            answer = "当前用户分层结果：" + "，".join(parts) + "。"
        else:
            answer = "当前还没有足够的 RFM 分层结果，可以先触发分析计算或导入更多订单。"
        suggestions = ["高价值用户做会员权益", "潜力用户做复购券", "流失用户做低频召回"]
    elif any(word in lowered for word in ["关联", "搭配", "推荐", "组合", "一起"]):
        rules = calculate_association(db, limit=5)
        if rules:
            lines = []
            for rule in rules:
                left = "、".join(rule.get("antecedent_names") or rule.get("antecedents") or [])
                right = "、".join(rule.get("consequent_names") or rule.get("consequents") or [])
                lines.append(f"购买「{left}」后可推荐「{right}」，置信度 {rule.get('confidence', 0):.2f}，提升度 {rule.get('lift', 0):.2f}")
            answer = "可以参考这些商品搭配：\n" + "\n".join(lines)
        else:
            answer = "当前订单共购数据不足，还没有形成稳定的商品关联规则。"
        suggestions = ["把高提升度组合放到详情页和购物车", "组合推荐前先确认库存", "优先使用高置信度规则做自动推荐"]
    else:
        m = summary["metrics"]
        top = summary["top_products"][0]["name"] if summary["top_products"] else "暂无"
        answer = (
            f"整体看，累计销售额 {m['total_sales']:.2f} 元，成交 {m['total_orders']} 单，"
            f"客单价 {m['avg_order_value']:.2f} 元。近 30 天成交 {m['recent_30d_orders']} 单，"
            f"热销代表商品是「{top}」。"
        )
        suggestions = [item["content"] for item in summary["insights"][:3]]

    knowledge = search_knowledge(q)
    return {
        "answer": answer,
        "suggestions": suggestions,
        "sources": sources,
        "related_knowledge": knowledge,
    }
