from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, contains_eager

from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import login_required, get_current_user
from lation.modules.customer.models.product import Order, OrderPlan, Plan, Product
from lation.modules.customer.models.subscription import Subscription
from lation.modules.customer.routers.schemas import CreateSubscriptionSchema, SubscriptionSchema


router = APIRouter()

@router.get('/subscriptions',
            tags=['subscription'],
            dependencies=[Depends(login_required)],
            response_model=Response[List[SubscriptionSchema]])
def list_subscriptionss(is_active:Optional[bool]=None,
                        end_user=Depends(get_current_user),
                        session:Session=Depends(get_session)):
    query = session.query(Subscription)\
        .join(Subscription.order_plan)\
        .join(OrderPlan.order)\
        .join(OrderPlan.plan)\
        .join(Order.payment)\
        .join(Plan.product)\
        .filter(Order.end_user_id == end_user.id)\
        .options(
            contains_eager(Subscription.order_plan)
                .contains_eager(OrderPlan.order)
                .noload(Order.order_plans))\
        .options(
            contains_eager(Subscription.order_plan)
                .contains_eager(OrderPlan.plan)
                .contains_eager(Plan.product)
                .noload(Product.plans))
    if is_active == True:
        query = query.filter(Subscription.unsubscribe_time == None)
    elif is_active == False:
        query = query.filter(Subscription.unsubscribe_time != None)
    subscriptions = query.all()
    return Response[List[SubscriptionSchema]](status=StatusEnum.SUCCESS, data=subscriptions)


@router.post('/subscriptions',
             tags=['subscription'],
             dependencies=[Depends(login_required)],
             response_model=Response[SubscriptionSchema])
@managed_transaction
def create_subscription(subscription_data:CreateSubscriptionSchema,
                        end_user=Depends(get_current_user),
                        session:Session=Depends(get_session)):
    order_plan = session.query(OrderPlan).get(subscription_data.order_plan_id)
    if not order_plan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid order plan id')
    if order_plan.order.end_user_id != end_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid order plan id')
    subscription = session.query(Subscription)\
        .filter(Subscription.order_plan_id == order_plan.id,
                Subscription.unsubscribe_time == None)\
        .one_or_none()
    if subscription:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Duplicate subscription')
    subscription = Subscription(order_plan=order_plan, subscribe_time=datetime.utcnow())
    session.add(subscription)
    session.flush()
    return Response[SubscriptionSchema](status=StatusEnum.SUCCESS, data=subscription)


@router.post('/subscriptions/{subscription_id}/unsubscribe',
             tags=['subscription'],
             dependencies=[Depends(login_required)],
             response_model=Response)
@managed_transaction
def unsubscribe_subscription(subscription_id:int,
                             end_user=Depends(get_current_user),
                             session:Session=Depends(get_session)):
    subscription = session.query(Subscription).get(subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid subscription id')
    if subscription.unsubscribe_time:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid subscription id')
    if subscription.order_plan.order.end_user_id != end_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid subscription id')
    subscription.unsubscribe()
    return Response(status=StatusEnum.SUCCESS)
