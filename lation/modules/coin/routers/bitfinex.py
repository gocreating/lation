from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends

from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient, FundingCreditSchema, FundingOfferSchema, LedgerSchema, UpdateFundingOfferSchema, WalletSchema
from lation.modules.coin.dependencies import get_bitfinex_api_client
from lation.modules.coin.models.job import get_bitfinex_funding_market_recommended_ask_rate
from lation.modules.coin.routers.schemas import BitfinexMetricsSchema
from lation.modules.customer.dependencies import login_required, subscription_required


router = APIRouter()

@router.get('/metrics/bitfinex', tags=['bitfinex'], response_model=Response[BitfinexMetricsSchema])
async def get_bitfinex_metrics():
    return Response[BitfinexMetricsSchema](status=StatusEnum.SUCCESS, data={
        'funding_market_recommended_ask_rate': get_bitfinex_funding_market_recommended_ask_rate()
    })

@router.get('/wallets',
            tags=['bitfinex'],
            dependencies=[Depends(login_required), Depends(subscription_required(['CFB']))],
            response_model=Response[List[WalletSchema]])
async def list_wallets(bitfinex_api_client=Depends(get_bitfinex_api_client)):
    wallets = bitfinex_api_client.get_user_wallets()
    return Response[List[WalletSchema]](status=StatusEnum.SUCCESS, data=wallets)

@router.get('/ledgers/{currency}/30-day-interest-payments',
            tags=['bitfinex'],
            dependencies=[Depends(login_required), Depends(subscription_required(['CFB']))],
            response_model=Response[List[LedgerSchema]])
async def list_30_day_interest_ledgers(currency:BitfinexAPIClient.CurrencyEnum,
                                       bitfinex_api_client=Depends(get_bitfinex_api_client)):
    utc_now = datetime.utcnow()
    start = utc_now - timedelta(days=30)
    ledgers = bitfinex_api_client.get_user_ledgers(currency, start=start, end=utc_now, limit=40, category=BitfinexAPIClient.LedgerCategoryEnum.MARGIN_SWAP_INTEREST_PAYMENT)
    return Response[List[LedgerSchema]](status=StatusEnum.SUCCESS, data=ledgers)

@router.get('/funding/credits/{symbol}',
            tags=['bitfinex'],
            dependencies=[Depends(login_required), Depends(subscription_required(['CFB']))],
            response_model=Response[List[FundingCreditSchema]])
async def list_funding_credits(symbol:str, bitfinex_api_client=Depends(get_bitfinex_api_client)):
    funding_credits = bitfinex_api_client.get_user_funding_credits(symbol)
    return Response[List[FundingCreditSchema]](status=StatusEnum.SUCCESS, data=funding_credits)

@router.get('/funding/offers/{symbol}',
            tags=['bitfinex'],
            dependencies=[Depends(login_required), Depends(subscription_required(['CFB']))],
            response_model=Response[List[FundingOfferSchema]])
async def list_funding_credits(symbol:str, bitfinex_api_client=Depends(get_bitfinex_api_client)):
    funding_offers = bitfinex_api_client.get_user_funding_offers(symbol)
    return Response[List[FundingOfferSchema]](status=StatusEnum.SUCCESS, data=funding_offers)

@router.post('/funding/offers/{offer_id}/cancel',
             tags=['bitfinex'],
             dependencies=[Depends(login_required), Depends(subscription_required(['CFB']))],
             response_model=Response[UpdateFundingOfferSchema])
async def cancel_funding_offer(offer_id:int, bitfinex_api_client=Depends(get_bitfinex_api_client)):
    cancel_funding_offer = bitfinex_api_client.cancel_user_funding_offer(offer_id)
    return Response[UpdateFundingOfferSchema](status=StatusEnum.SUCCESS, data=cancel_funding_offer)
