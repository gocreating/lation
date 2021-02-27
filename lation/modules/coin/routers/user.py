from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.coin.models.config import EndUserBitfinexConfig
from lation.modules.coin.routers.schemas import EndUserBitfinexConfigSchema
from lation.modules.customer.dependencies import login_required, get_current_user


router = APIRouter()

@router.get('/configs/bitfinex',
            tags=['end_user'],
            dependencies=[Depends(login_required)],
            response_model=Response[EndUserBitfinexConfigSchema])
def get_bitfinex_config(end_user=Depends(get_current_user), session:Session=Depends(get_session)):
    return Response[EndUserBitfinexConfigSchema](status=StatusEnum.SUCCESS, data=end_user.end_user_bitfinex_config)

@router.patch('/configs/bitfinex',
             tags=['end_user'],
             dependencies=[Depends(login_required)],
             response_model=Response[EndUserBitfinexConfigSchema])
@managed_transaction
def update_bitfinex_config(config:EndUserBitfinexConfigSchema,
                           end_user=Depends(get_current_user), session:Session=Depends(get_session)):
    end_user_bitfinex_config = end_user.end_user_bitfinex_config
    if not end_user_bitfinex_config:
        end_user_bitfinex_config = EndUserBitfinexConfig(end_user=end_user)
        session.add(end_user_bitfinex_config)
    if config.api_key:
        end_user_bitfinex_config.api_key = config.api_key
    if config.api_secret:
        end_user_bitfinex_config.api_secret = config.api_secret
    if config.config:
        end_user_bitfinex_config.config = config.config
    return Response[EndUserBitfinexConfigSchema](status=StatusEnum.SUCCESS, data=end_user_bitfinex_config)
