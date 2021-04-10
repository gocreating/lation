from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from lation.modules.coin.dependencies import get_current_ftx_rest_api_client


router = APIRouter()

def min_price_increment(a: float, b: float):
    # actually this should be float-version lcm(a, b)
    return max(a, b)

@router.get('/ftx/spot-perp-pairs', tags=['ftx'])
async def list_pairs(api_client=Depends(get_current_ftx_rest_api_client)):
    markets = client.list_markets()
    futures = client.list_futures()
    funding_rates = client.list_funding_rates()

    market_map = {market['name']: market
                  for market in markets
                  if market['enabled']}
    spot_map = {market['baseCurrency']: market
                for _, market in market_map.items()
                if market['type'] == 'spot' and market['quoteCurrency'] == 'USD'}
    perp_map = {future['underlying']: future for future in futures if future['enabled'] and future['perpetual']}
    funding_rate_map = {funding_rate['future']: funding_rate for funding_rate in funding_rates}

    pair_currencies = set(spot_map.keys()).intersection(set(perp_map.keys()))
    pairs = [{
        'currency': spot_map[currency]['baseCurrency'],
        'spot_name': spot_map[currency]['name'],
        'spot_volume_usd_24h': spot_map[currency]['volumeUsd24h'],
        'perp_name': perp_map[currency]['name'],
    } for currency in pair_currencies]
    pairs = [{
        **pair,
        'funding_rate_1h': funding_rate_map[pair['perp_name']]['rate'],
        'funding_rate_30d': funding_rate_map[pair['perp_name']]['rate'] * 24 * 30,
        # 'spot_min_provide_size': market_map[pair['spot_name']]['minProvideSize'],
        # 'spot_price_increment': market_map[pair['spot_name']]['priceIncrement'],
        'spot_size_increment': market_map[pair['spot_name']]['sizeIncrement'],
        # 'perp_min_provide_size': market_map[pair['perp_name']]['minProvideSize'],
        # 'perp_price_increment': market_map[pair['perp_name']]['priceIncrement'],
        'perp_size_increment': market_map[pair['perp_name']]['sizeIncrement'],
        # 'lcm_price_increment': lcm(market_map[pair['spot_name']]['priceIncrement'], market_map[pair['perp_name']]['priceIncrement']),
        'min_provide_size': max(market_map[pair['spot_name']]['minProvideSize'],
                                market_map[pair['perp_name']]['minProvideSize']),
        'price_increment': min_price_increment(market_map[pair['spot_name']]['priceIncrement'], market_map[pair['perp_name']]['priceIncrement']),
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
