import enum
from typing import Optional

from fastapi import Depends, HTTPException, status

from lation.core.env import get_env
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient
from lation.modules.coin.ftx import FTXRestAPIClient, FTXSpotFuturesArbitrageStrategy
from lation.modules.customer.dependencies import login_required, get_current_user


FTX_API_KEY = get_env('FTX_API_KEY')
FTX_API_SECRET = get_env('FTX_API_SECRET')

class SubaccountNameEnum(str, enum.Enum):
    期现套利子帳戶 = '期现套利子帳戶'
    媽媽 = '媽媽'

async def get_bitfinex_api_client(end_user=Depends(get_current_user)) -> BitfinexAPIClient:
    end_user_bitfinex_config = end_user.end_user_bitfinex_config
    if not end_user_bitfinex_config:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bitfinex config not found')
    if not end_user_bitfinex_config.api_key or not end_user_bitfinex_config.api_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid bitfinex credential config')
    bitfinex_api_client = BitfinexAPIClient(api_key=end_user_bitfinex_config.api_key,
                                            api_secret=end_user_bitfinex_config.api_secret)
    return bitfinex_api_client

async def get_current_ftx_rest_api_client(subaccount_name: Optional[SubaccountNameEnum] = None) -> FTXRestAPIClient:
    # TODO: read api_key, api_secret, and subaccount_name from current_user's config
    ftx_rest_api_client = FTXRestAPIClient(api_key=FTX_API_KEY,
                                           api_secret=FTX_API_SECRET,
                                           subaccount_name=subaccount_name)
    return ftx_rest_api_client

async def get_current_ftx_spot_futures_arbitrage_strategy(subaccount_name: Optional[SubaccountNameEnum] = None) -> FTXSpotFuturesArbitrageStrategy:
    from lation.modules.coin.models.job import ftx_spot_futures_arbitrage_strategies
    strategy = next((strategy for strategy in ftx_spot_futures_arbitrage_strategies
                    if strategy.rest_api_client.subaccount_name == subaccount_name), None)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='FTX spot futures arbitrage strategy not found')
    return strategy
