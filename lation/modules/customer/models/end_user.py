from datetime import datetime
from typing import List

from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser
from lation.modules.customer.models.product import Order, OrderPlan, Plan, Product
from lation.modules.customer.models.subscription import Subscription


def is_subscribed_to_any_products(self, product_codes: List[str]):
    session = object_session(self)
    utc_now = datetime.utcnow()
    inforce_subscriptions = session.query(Subscription)\
        .join(Subscription.order_plan)\
        .join(OrderPlan.order)\
        .join(OrderPlan.plan)\
        .join(Plan.product)\
        .filter(Subscription.subscribe_time <= utc_now, utc_now < Subscription.due_time)\
        .filter(Order.end_user == self)\
        .filter(Order.state == Order.StateEnum.EFFECTIVE.value)\
        .filter(Product.code.in_(product_codes))\
        .limit(1)\
        .all()
    return len(inforce_subscriptions) > 0

EndUser.is_subscribed_to_any_products = is_subscribed_to_any_products
