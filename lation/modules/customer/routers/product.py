from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, contains_eager

from lation.modules.base.models.payment import ECPayPaymentGatewayTrade, PaymentGateway
from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import login_required, get_current_user, get_payment_gateway
from lation.modules.customer.models.product import Product, Plan, Order, OrderPlan
from lation.modules.customer.routers.schemas import CreateOrderSchema, OrderSchema, PrimitiveOrderSchema, ProductSchema


router = APIRouter()

def verify_ecpay_request(session:Session, CustomField3:str, CustomField4:str):
    if CustomField3 != 'order_id':
        return False, None
    order_id = CustomField4
    order = session.query(Order).get(order_id)
    if not order:
        return False, order
    return True, order

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


# https://www.ecpay.com.tw/Content/files/ecpay_011.pdf (p.36)
@router.post('/payment/ecpay/callback',
             tags=['product'])
@managed_transaction
async def payment_ecpay_callback(MerchantID:str=Form(None),
                                 MerchantTradeNo:str=Form(None),
                                 StoreID:str=Form(None),
                                 RtnCode:int=Form(None),
                                 RtnMsg:str=Form(None),
                                 TradeNo:str=Form(None),
                                 TradeAmt:int=Form(None),
                                 PaymentDate:str=Form(None),
                                 PaymentType:str=Form(None),
                                 PaymentTypeChargeFee:float=Form(None),
                                 TradeDate:str=Form(None),
                                 SimulatePaid:int=Form(None),
                                 CustomField1:str=Form(None),
                                 CustomField2:str=Form(None),
                                 CustomField3:str=Form(None),
                                 CustomField4:str=Form(None),
                                 CheckMacValue:str=Form(None),
                                 payment_gateway=Depends(get_payment_gateway),
                                 session:Session=Depends(get_session)):
    is_verified, order = verify_ecpay_request(session, CustomField3, CustomField4)

    ecpay_payment_gateway_trade = session.query(ECPayPaymentGatewayTrade).filter(ECPayPaymentGatewayTrade.number == MerchantTradeNo).one()
    ecpay_payment_gateway_trade.reference = TradeNo
    ecpay_payment_gateway_trade.trade_amt = TradeAmt
    # https://github.com/tiangolo/fastapi/issues/309
    # https://github.com/tiangolo/fastapi/issues/2433
    ecpay_payment_gateway_trade.rtn_msg = RtnMsg.encode('Latin-1').decode('utf-8')
    ecpay_payment_gateway_trade.rtn_code = RtnCode

    if not is_verified or RtnCode != 1:
        order.charge_fail()
        return '0|err'
    order.charge_success(ecpay_payment_gateway_trade)
    return '1|OK'

@router.post('/payment/ecpay/order-result/callback',
             tags=['product'])
async def payment_ecpay_callback(RtnCode:int=Form(None),
                                 CustomField3:str=Form(None),
                                 CustomField4:str=Form(None),
                                 payment_gateway=Depends(get_payment_gateway),
                                 session:Session=Depends(get_session)):
    is_verified, _ = verify_ecpay_request(session, CustomField3, CustomField4)
    if not is_verified or RtnCode != 1:
        return RedirectResponse(url=payment_gateway.get_failure_redirect_url(error='The payment is failed'))
    return RedirectResponse(url=payment_gateway.get_success_redirect_url())
