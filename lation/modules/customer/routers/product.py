from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, contains_eager

from lation.modules.base.models.payment import PaymentGateway
from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import login_required, get_current_user
from lation.modules.customer.models.product import Product, Plan, Order, OrderPlan
from lation.modules.customer.routers.schemas import CreateOrderSchema, OrderSchema, PrimitiveOrderSchema, ProductSchema


router = APIRouter()

@router.get('/products',
            tags=['product'],
            response_model=Response[List[ProductSchema]])
async def list_products(session:Session=Depends(get_session)):
    products = session.query(Product)\
        .outerjoin(Product.plans)\
        .options(
            contains_eager(Product.plans)
                .noload(Plan.product))\
        .all()
    return Response[List[ProductSchema]](status=StatusEnum.SUCCESS, data=products)


@router.get('/orders',
            tags=['product'],
            dependencies=[Depends(login_required)],
            response_model=Response[List[OrderSchema]])
@managed_transaction
async def list_orders(end_user=Depends(get_current_user),
                session:Session=Depends(get_session)):
    orders = session.query(Order)\
        .filter(Order.end_user_id == end_user.id, Order.state.in_([Order.StateEnum.EFFECTIVE.value]))\
        .options(
            contains_eager(Order.order_plans)
                .noload(OrderPlan.order))\
        .options(
            contains_eager(Order.order_plans)
                .contains_eager(OrderPlan.plan)
                .contains_eager(Plan.product)
                .noload(Product.plans))\
        .all()
    return Response[List[OrderSchema]](status=StatusEnum.SUCCESS, data=orders)


@router.post('/orders',
            tags=['product'],
            dependencies=[Depends(login_required)],
            response_model=Response[PrimitiveOrderSchema])
@managed_transaction
async def create_order(order_data:CreateOrderSchema,
                 end_user=Depends(get_current_user),
                 session:Session=Depends(get_session)):
    plan = session.query(Plan).get(order_data.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid plan id')
    orders = session.query(Order)\
        .join(Order.order_plans)\
        .filter(Order.state == Order.StateEnum.EFFECTIVE.value,
                Order.end_user_id == end_user.id,
                OrderPlan.plan_id == plan.id)\
        .all()
    if plan.max_end_user_effective_order_count != None:
        if len(orders) >= plan.max_end_user_effective_order_count:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Plan quota limited')
    product = plan.product
    if product.max_end_user_effective_order_count != None:
        if len(orders) >= product.max_end_user_effective_order_count:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Product quota limited')
    order = Order(end_user_id=end_user.id,
                  order_plans=[OrderPlan(plan_id=plan.id)])
    session.add(order)
    session.flush()
    return Response[PrimitiveOrderSchema](status=StatusEnum.SUCCESS, data=order)


@router.get('/orders/{order_id}/charge',
            tags=['product'],
            dependencies=[Depends(login_required)])
@managed_transaction
async def charge_order(order_id:int, payment_gateway_id:int, session:Session=Depends(get_session)):
    order = session.query(Order).get(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Order not found')
    payment_gateway = session.query(PaymentGateway).get(payment_gateway_id)
    if not payment_gateway:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid payment gateway')
    payment_page_content = order.charge(payment_gateway)
    if order.state == Order.StateEnum.PENDING_PAYMENT.value:
        return HTMLResponse(content=payment_page_content)
    elif order.state == Order.StateEnum.EFFECTIVE.value:
        return RedirectResponse(url=payment_gateway.get_success_redirect_url())
    elif order.state == Order.StateEnum.PAYMENT_FAILED.value:
        return RedirectResponse(url=payment_gateway.get_failure_redirect_url(error='The payment is failed'))
