import statistics

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from lation.modules.coin.dependencies import get_current_ftx_rest_api_client
from lation.modules.coin.ftx import FTXManager, ftx_manager


router = APIRouter()


@router.get('/ftx/spot-perp-pairs', tags=['ftx'])
async def list_pairs(api_client=Depends(get_current_ftx_rest_api_client)):
    market_name_map = ftx_manager.market_name_map
    spot_base_currency_map = ftx_manager.spot_base_currency_map
    perp_underlying_map = ftx_manager.perp_underlying_map
    funding_rate_name_map = ftx_manager.funding_rate_name_map

    pair_currencies = set(spot_base_currency_map.keys()).intersection(set(perp_underlying_map.keys()))
    pairs = [{
        'currency': spot_base_currency_map[currency]['baseCurrency'],
        'spot_name': spot_base_currency_map[currency]['name'],
        'spot_volume_usd_24h': spot_base_currency_map[currency]['volumeUsd24h'],
        'perp_name': perp_underlying_map[currency]['name'],
    } for currency in pair_currencies]
    pairs = [{
        **pair,
        'min_provide_size': max(
            market_name_map[pair['spot_name']]['minProvideSize'],
            market_name_map[pair['perp_name']]['minProvideSize']
        ),
        'size_increment': FTXManager.lowest_common_size_increment(
            market_name_map[pair['spot_name']]['sizeIncrement'],
            market_name_map[pair['perp_name']]['sizeIncrement']
        ),
        'price_increment': FTXManager.lowest_common_price_increment(
            market_name_map[pair['spot_name']]['priceIncrement'],
            market_name_map[pair['perp_name']]['priceIncrement']
        ),
        'funding_rate_1h': Decimal(funding_rate_name_map[pair['perp_name']]['rate']),
    } for pair in pairs]

    pairs = [{
        **pair,
        'funding_rate_30d': pair['funding_rate_1h'] * 24 * 30,
        'funding_rate_1y': pair['funding_rate_1h'] * 24 * 365,
    } for pair in pairs]

    pairs = sorted(pairs, key=lambda p: p['spot_volume_usd_24h'], reverse=True)
    pairs = [{
        **pair,
        'spot_volume_usd_24h_rank': rank + 1,
    } for rank, pair in enumerate(pairs)]

    pairs = sorted(pairs, key=lambda p: p['funding_rate_1h'], reverse=True)
    pairs = [{
        **pair,
        'funding_rate_1h_rank': rank + 1,
    } for rank, pair in enumerate(pairs)]

    pairs = sorted(pairs, key=lambda p: p['spot_volume_usd_24h_rank'] + p['funding_rate_1h_rank'])
    return pairs

@router.get('/ftx/account/leverage', tags=['ftx'])
async def get_account_leverage(api_client=Depends(get_current_ftx_rest_api_client)):
    leverage = ftx_manager.get_leverage(rest_api_client=api_client)
    return leverage

@router.get('/ftx/funding-payments/30d', tags=['ftx'])
async def list_funding_payments(api_client=Depends(get_current_ftx_rest_api_client)):
    funding_payments_30d = api_client.list_funding_payments(start_time=datetime.now() - timedelta(days=30),
                                                            end_time=datetime.now())
    return funding_payments_30d

@router.get('/ftx/summary', tags=['ftx'])
async def get_summary(api_client=Depends(get_current_ftx_rest_api_client)):
    leverage = ftx_manager.get_leverage(rest_api_client=api_client)
    funding_payments_30d = api_client.list_funding_payments(start_time=datetime.now() - timedelta(days=30),
                                                            end_time=datetime.now())
    future_names = set([p['future'] for p in funding_payments_30d])
    future_funding_payment_map = {
        future_name: {
            'total_usd': -sum([p['payment'] for p in funding_payments_30d if p['future'] == future_name]),
            'mean_rate_1h': statistics.mean([p['rate'] for p in funding_payments_30d if p['future'] == future_name]),
            'mean_rate_1y': statistics.mean([p['rate'] for p in funding_payments_30d if p['future'] == future_name]) * 24 * 365,
        }
        for future_name in future_names
    }
    return {
        'leverage': leverage,
        'funding_payment_count': len(funding_payments_30d),
        'funding_payment': future_funding_payment_map
    }

@router.post('/ftx/orders/spot-perp/{base_currency}', tags=['ftx'])
async def create_order(base_currency:str,
                       base_amount:Optional[str]=None,
                       quote_currency:Optional[Literal['USD', 'USDT']]='USD', quote_amount:Optional[str]=None,
                       api_client=Depends(get_current_ftx_rest_api_client)):
    if base_amount:
        base_amount = Decimal(base_amount)
    if quote_amount:
        quote_amount = Decimal(quote_amount)
    try:
        spot_order, perp_order = await ftx_manager.place_spot_perp_order(base_currency,
                                                                        base_amount=base_amount,
                                                                        quote_currency=quote_currency,
                                                                        quote_amount=quote_amount,
                                                                        rest_api_client=api_client)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return {
        'spot_order': spot_order,
        'perp_order': perp_order,
    }
