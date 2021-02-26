from fastapi import APIRouter

from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient
from lation.modules.coin.models.job import get_funding_market_recommended_sell_rate


router = APIRouter()

@router.get('/market/funding/recommended-sell-rate', tags=['bitfinex'])
async def get_recommended_sell_rate():
    return get_funding_market_recommended_sell_rate()
