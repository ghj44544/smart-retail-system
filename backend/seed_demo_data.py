import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from passlib.context import CryptContext

from app.models.base import Base, SessionLocal, engine
from app.models.behavior import Behavior
from app.models.category import Category
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.services.analysis_service import calculate_cluster, calculate_rfm


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CATEGORIES = ["电子数码", "服装鞋包", "家居生活", "食品饮料", "运动户外", "美妆个护", "图书文具", "母婴玩具"]

PRODUCTS = [
    ("DEMO-P001", "无线蓝牙耳机 Pro", "电子数码", 299, 4.8),
    ("DEMO-P002", "智能手表 S3", "电子数码", 899, 4.6),
    ("DEMO-P003", "Type-C 快充线 1m", "电子数码", 29.9, 4.5),
    ("DEMO-P004", "便携充电宝 20000mAh", "电子数码", 129, 4.7),
    ("DEMO-P005", "机械键盘 RGB", "电子数码", 299, 4.8),
    ("DEMO-P006", "无线静音鼠标", "电子数码", 129, 4.4),
    ("DEMO-P007", "男士休闲夹克", "服装鞋包", 359, 4.3),
    ("DEMO-P008", "女士针织连衣裙", "服装鞋包", 259, 4.5),
    ("DEMO-P009", "轻量运动跑鞋", "服装鞋包", 499, 4.6),
    ("DEMO-P010", "纯棉基础 T 恤", "服装鞋包", 99, 4.2),
    ("DEMO-P011", "智能护眼台灯", "家居生活", 159, 4.7),
    ("DEMO-P012", "保温杯 500ml", "家居生活", 89, 4.5),
    ("DEMO-P013", "乳胶枕头", "家居生活", 199, 4.4),
    ("DEMO-P014", "桌面收纳箱套装", "家居生活", 79, 4.1),
    ("DEMO-P015", "坚果礼盒", "食品饮料", 168, 4.6),
    ("DEMO-P016", "有机绿茶", "食品饮料", 88, 4.3),
    ("DEMO-P017", "进口咖啡豆", "食品饮料", 129, 4.8),
    ("DEMO-P018", "低脂燕麦片", "食品饮料", 59, 4.2),
    ("DEMO-P019", "瑜伽垫", "运动户外", 79, 4.4),
    ("DEMO-P020", "羽毛球拍套装", "运动户外", 249, 4.6),
    ("DEMO-P021", "登山双肩包", "运动户外", 399, 4.5),
    ("DEMO-P022", "智能跳绳", "运动户外", 49, 4.1),
    ("DEMO-P023", "防晒霜 SPF50", "美妆个护", 129, 4.7),
    ("DEMO-P024", "氨基酸洗面奶", "美妆个护", 89, 4.5),
    ("DEMO-P025", "补水面膜 20片", "美妆个护", 119, 4.4),
    ("DEMO-P026", "护手霜礼盒", "美妆个护", 69, 4.2),
    ("DEMO-P027", "Python 编程入门", "图书文具", 59, 4.8),
    ("DEMO-P028", "数据分析实战", "图书文具", 79, 4.7),
    ("DEMO-P029", "手账本套装", "图书文具", 39, 4.3),
    ("DEMO-P030", "速干中性笔 12支", "图书文具", 24.9, 4.2),
    ("DEMO-P031", "婴儿纸尿裤 L码", "母婴玩具", 139, 4.6),
    ("DEMO-P032", "益智积木套装", "母婴玩具", 199, 4.5),
]

USER_NAMES = [
    ("demo001", "林晓雨"), ("demo002", "陈一帆"), ("demo003", "周明轩"), ("demo004", "赵安琪"),
    ("demo005", "吴晨"), ("demo006", "郑佳宁"), ("demo007", "孙浩然"), ("demo008", "唐诗涵"),
    ("demo009", "何宇航"), ("demo010", "郭静怡"), ("demo011", "马思远"), ("demo012", "朱可欣"),
    ("demo013", "胡嘉乐"), ("demo014", "高雅婷"), ("demo015", "罗子墨"), ("demo016", "梁悦"),
    ("demo017", "宋星辰"), ("demo018", "沈若溪"),
]


def get_or_create_category(db, name):
    category = db.query(Category).filter(Category.name == name).first()
    if category:
        return category
    category = Category(name=name)
    db.add(category)
    db.flush()
    return category


def seed_categories_and_products(db):
    categories = {name: get_or_create_category(db, name) for name in CATEGORIES}
    products = []
    for product_no, name, category_name, price, rating in PRODUCTS:
        product = db.query(Product).filter(Product.product_no == product_no).first()
        if not product:
            product = Product(
                product_no=product_no,
                name=name,
                description=f"{name}，适合智能零售系统演示的精选商品。",
                category_id=categories[category_name].id,
                price=Decimal(str(price)),
                stock=random.randint(120, 1800),
                status="on",
                sales_count=0,
                rating=Decimal(str(rating)),
            )
            db.add(product)
            db.flush()
        products.append(product)
    return products


def seed_users(db):
    users = []
    for username, nickname in USER_NAMES:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(
                username=username,
                password=pwd_context.hash("user123"),
                role="user",
                nickname=nickname,
                email=f"{username}@demo.retail",
                phone=f"139{random.randint(10000000, 99999999)}",
                created_at=datetime.utcnow() - timedelta(days=random.randint(20, 180)),
            )
            db.add(user)
            db.flush()
        users.append(user)
    return users


def seed_orders_and_behaviors(db, users, products):
    existing_demo_orders = db.query(Order).filter(Order.order_no.like("DEMO-ORD-%")).count()
    target_orders = 96
    if existing_demo_orders >= target_orders:
        return

    product_groups = {
        "electronics": products[0:6],
        "fashion": products[6:10],
        "home": products[10:14],
        "food": products[14:18],
        "sport": products[18:22],
        "beauty": products[22:26],
        "book": products[26:30],
        "baby": products[30:32],
    }
    preferences = list(product_groups.values())
    order_index = existing_demo_orders + 1

    for user_index, user in enumerate(users):
        primary = preferences[user_index % len(preferences)]
        secondary = preferences[(user_index + 2) % len(preferences)]
        order_count = random.randint(3, 7)

        for _ in range(order_count):
            created_at = datetime.utcnow() - timedelta(
                days=random.randint(0, 58),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )
            item_pool = primary + random.sample(secondary, min(2, len(secondary)))
            item_count = random.randint(1, min(4, len(item_pool)))
            chosen = random.sample(item_pool, item_count)
            status = random.choices(
                ["completed", "paid", "shipped", "pending", "cancelled"],
                weights=[62, 14, 12, 8, 4],
                k=1,
            )[0]

            order = Order(
                order_no=f"DEMO-ORD-{order_index:04d}",
                user_id=user.id,
                total_amount=Decimal("0.00"),
                status=status,
                created_at=created_at,
                paid_at=created_at + timedelta(minutes=random.randint(5, 90)) if status in {"paid", "shipped", "completed"} else None,
                completed_at=created_at + timedelta(days=random.randint(1, 5)) if status == "completed" else None,
            )
            db.add(order)
            db.flush()

            total = Decimal("0.00")
            for product in chosen:
                quantity = random.randint(1, 3)
                price = Decimal(str(product.price))
                total += price * quantity
                db.add(OrderItem(order_id=order.id, product_id=product.id, price=price, quantity=quantity, created_at=created_at))
                if status == "completed":
                    product.sales_count = (product.sales_count or 0) + quantity

            order.total_amount = total
            order_index += 1

            for product in random.sample(item_pool, min(len(item_pool), random.randint(3, 6))):
                view_time = created_at - timedelta(days=random.randint(0, 9), hours=random.randint(1, 20))
                db.add(Behavior(user_id=user.id, product_id=product.id, behavior_type="view", created_at=view_time))
                if random.random() < 0.45:
                    db.add(Behavior(user_id=user.id, product_id=product.id, behavior_type="favorite", created_at=view_time + timedelta(minutes=10)))
                if random.random() < 0.55:
                    db.add(Behavior(user_id=user.id, product_id=product.id, behavior_type="cart", created_at=view_time + timedelta(hours=1)))
            if status in {"paid", "shipped", "completed"}:
                for product in chosen:
                    db.add(Behavior(user_id=user.id, product_id=product.id, behavior_type="buy", created_at=created_at))


def main():
    random.seed(20260529)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        products = seed_categories_and_products(db)
        users = seed_users(db)
        seed_orders_and_behaviors(db, users, products)
        db.commit()
        calculate_rfm(db)
        calculate_cluster(db, n_clusters=5)
        counts = {
            "users": db.query(User).count(),
            "categories": db.query(Category).count(),
            "products": db.query(Product).count(),
            "orders": db.query(Order).count(),
            "order_items": db.query(OrderItem).count(),
            "behaviors": db.query(Behavior).count(),
        }
        print(counts)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
