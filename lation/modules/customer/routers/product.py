from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, contains_eager

from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import login_required, get_current_user
from lation.modules.customer.models.product import Product, Plan, Order, OrderPlan
from lation.modules.customer.routers.schemas import CreateOrderSchema, OrderSchema, ProductSchema


router = APIRouter()

@router.get('/products',
            tags=['product'],
            response_model=Response[List[ProductSchema]])
def list_product(session:Session=Depends(get_session)):
    products = session.query(Product)\
        .outerjoin(Product.plans)\
        .options(contains_eager(Product.plans))\
        .all()
    return Response[List[ProductSchema]](status=StatusEnum.SUCCESS, data=products)


@router.get('/orders',
            tags=['product'],
            dependencies=[Depends(login_required)],
            response_model=Response[List[OrderSchema]])
@managed_transaction
def list_orders(end_user=Depends(get_current_user),
                 session:Session=Depends(get_session)):
    orders = session.query(Order)\
        .filter(Order.end_user_id == end_user.id)\
        .all()
    return Response[List[OrderSchema]](status=StatusEnum.SUCCESS, data=orders)


@router.post('/orders',
            tags=['product'],
            dependencies=[Depends(login_required)],
            response_model=Response[OrderSchema])
@managed_transaction
def create_order(order_data:CreateOrderSchema,
                 end_user=Depends(get_current_user),
                 session:Session=Depends(get_session)):
    plan = session.query(Plan).get(order_data.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid plan id')
    orders = session.query(Order)\
        .join(Order.order_plans)\
        .filter(Order.end_user_id == end_user.id,
                OrderPlan.plan_id == plan.id)\
        .all()
    if len(orders) == 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Duplicate order')
    elif len(orders) > 1:
        raise NotImplementedError
    order = Order(end_user_id=end_user.id,
                  order_plans=[OrderPlan(plan_id=plan.id)],
                  purchase_time=datetime.utcnow())
    session.add(order)
    session.flush()
    return Response[OrderSchema](status=StatusEnum.SUCCESS, data=order)
