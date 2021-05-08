from fastapi import HTTPException, status

from lation.modules.spot_perp_bot.ftx import FTXSpotFuturesArbitrageStrategy
from lation.modules.spot_perp_bot.routers.schemas import SubaccountNameEnum


async def get_current_ftx_spot_futures_arbitrage_strategy(subaccount_name: SubaccountNameEnum = None) -> FTXSpotFuturesArbitrageStrategy:
    from lation.modules.spot_perp_bot.models.job import ftx_spot_futures_arbitrage_strategies

    strategy = next((strategy for strategy in ftx_spot_futures_arbitrage_strategies
                    if subaccount_name == None or strategy.rest_api_client.subaccount_name == subaccount_name.value), None)
    if not strategy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='FTX spot futures arbitrage strategy not found')
    return strategy
