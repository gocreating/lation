from datetime import datetime, timedelta

from sqlalchemy.orm import object_session

from lation.modules.customer.models.product import Order, OrderPlan, Plan
from lation.modules.customer.models.subscription import Subscription


def override_after_order_charge_sucess(self):
    session = object_session(self)

    # calculate subscribe_time
    # here we lock selected subscriptions to prevent race condition
    utc_now = datetime.utcnow()
    inforce_and_future_subscriptions = session\
        .query(Subscription)\
        .with_for_update(nowait=False)\
        .join(Subscription.order_plan)\
        .join(OrderPlan.order)\
        .join(OrderPlan.plan)\
        .join(Plan.product)\
        .filter(utc_now < Subscription.due_time)\
        .filter(Order.end_user == self.end_user)\
        .filter(Order.state == Order.StateEnum.EFFECTIVE.value)\
        .order_by(Subscription.due_time.desc())\
        .limit(1)\
        .all()
    if len(inforce_and_future_subscriptions) > 0:
        subscribe_time = inforce_and_future_subscriptions[0].due_time
    else:
        subscribe_time = datetime.utcnow()

    # calculate due_time
    plan_code = self.plans[0].code
    if plan_code == '7_DAY_FREE_TRIAL':
        due_time = subscribe_time + timedelta(days=7)
    elif plan_code == '1_MONTH':
        due_time = subscribe_time + timedelta(days=31)
    elif plan_code == '3_MONTH':
        due_time = subscribe_time + timedelta(days=93)
    else:
        raise NotImplementedError

    # instantiate subscription
    subscription = Subscription(order_plan=self.order_plans[0], subscribe_time=subscribe_time, due_time=due_time)
    session.add(subscription)

Order.after_order_charge_sucess = override_after_order_charge_sucess
