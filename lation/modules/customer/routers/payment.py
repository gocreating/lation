from typing import List

from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from lation.core.env import DEV
from lation.modules.base.models.payment import ECPayPaymentGateway
from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import get_current_platform
from lation.modules.customer.routers.schemas import PaymentGatewaySchema


router = APIRouter()

@router.get('/payment-gateways',
            tags=['payment'],
            response_model=Response[List[PaymentGatewaySchema]])
async def list_payment_gateways(platform=Depends(get_current_platform)):
    valid_payment_gateway_lation_ids = 'base.ecpay_staging_payment_gateway' if DEV else 'base.ecpay_payment_gateway'
    payment_gateways = [pg for pg in platform.payment_gateways if pg.lation_id in valid_payment_gateway_lation_ids]
    return Response[List[PaymentGatewaySchema]](status=StatusEnum.SUCCESS, data=payment_gateways)

# https://www.ecpay.com.tw/Content/files/ecpay_011.pdf (p.36)
@router.post('/payment-gateways/ecpay/callbacks/payment',
             tags=['payment'])
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
                                 session:Session=Depends(get_session)):
    try:
        ECPayPaymentGateway.handle_payment_result(session, {
            'MerchantID': MerchantID,
            'MerchantTradeNo': MerchantTradeNo,
            'StoreID': StoreID,
            'RtnCode': RtnCode,
            'RtnMsg': RtnMsg,
            'TradeNo': TradeNo,
            'TradeAmt': TradeAmt,
            'PaymentDate': PaymentDate,
            'PaymentType': PaymentType,
            'PaymentTypeChargeFee': PaymentTypeChargeFee,
            'TradeDate': TradeDate,
            'SimulatePaid': SimulatePaid,
            'CustomField1': CustomField1,
            'CustomField2': CustomField2,
            'CustomField3': CustomField3,
            'CustomField4': CustomField4,
            'CheckMacValue': CheckMacValue,
        })
        return '1|OK'
    except Exception as e:
        print(e)
        return '0|err'

@router.post('/payment-gateways/ecpay/callbacks/order-result',
             tags=['payment'])
async def payment_ecpay_callback(MerchantTradeNo:str=Form(None),
                                 RtnCode:int=Form(None),
                                 CustomField3:str=Form(None),
                                 CustomField4:str=Form(None),
                                 session:Session=Depends(get_session)):
    is_verified, trade = ECPayPaymentGateway.verify_payment_result(session, {
        'MerchantTradeNo': MerchantTradeNo,
        'RtnCode': RtnCode,
        'CustomField3': CustomField3,
        'CustomField4': CustomField4,
    })
    if not is_verified:
        return RedirectResponse(url=trade.payment_gateway.get_failure_redirect_url(error='The payment is failed'))
    return RedirectResponse(url=trade.payment_gateway.get_success_redirect_url())
