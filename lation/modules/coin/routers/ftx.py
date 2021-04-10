from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends
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
        'funding_rate_1h': Decimal(funding_rate_name_map[pair['perp_name']]['rate']),
        'spot_size_increment': market_name_map[pair['spot_name']]['sizeIncrement'],
        'perp_size_increment': market_name_map[pair['perp_name']]['sizeIncrement'],
        'min_provide_size': max(
            market_name_map[pair['spot_name']]['minProvideSize'],
            market_name_map[pair['perp_name']]['minProvideSize']
        ),
        'price_increment': FTXManager.lowest_common_price_increment(
            market_name_map[pair['spot_name']]['priceIncrement'],
            market_name_map[pair['perp_name']]['priceIncrement']
        ),
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

@router.post('/ftx/orders/spot-perp/{base_currency}', tags=['ftx'])
async def create_order(base_currency:str, api_client=Depends(get_current_ftx_rest_api_client)):
    # check balance
    # place spot order and perp order parallelly (asyncio.gather), should add short timeout when rate limit throttled
    pass
