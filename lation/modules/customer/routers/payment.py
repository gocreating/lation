from typing import List

from fastapi import APIRouter, Depends

from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import get_payment_gateway
from lation.modules.customer.routers.schemas import PaymentGatewaySchema


router = APIRouter()

@router.get('/payment-gateways',
            tags=['paymeny'],
            response_model=Response[List[PaymentGatewaySchema]])
async def list_payment_gateways(payment_gateway=Depends(get_payment_gateway)):
    return Response[List[PaymentGatewaySchema]](status=StatusEnum.SUCCESS, data=[payment_gateway])
