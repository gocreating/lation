from datetime import datetime

from sqlalchemy.orm import object_session

from lation.modules.customer.models.product import Order
from lation.modules.customer.models.subscription import Subscription


def override_after_order_charge_sucess(self):
    order_plan = self.order_plans[0]
    plan = order_plan.plan
    if plan.code == 'BASIC':
        session = object_session(self)
        subscription = Subscription(order_plan=order_plan, subscribe_time=datetime.utcnow())
        session.add(subscription)

Order.after_order_charge_sucess = override_after_order_charge_sucess
