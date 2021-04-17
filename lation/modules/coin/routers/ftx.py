import enum
import statistics
from collections import defaultdict

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from lation.modules.coin.dependencies import get_current_ftx_rest_api_client
from lation.modules.coin.ftx import FTXManager, ftx_manager


router = APIRouter()


class TimedeltaEnum(enum.Enum):
    HOUR_1 = 'HOUR_1'
    DAY_1 = 'DAY_1'
    DAY_30 = 'DAY_30'

def to_td(td: TimedeltaEnum):
    if td == TimedeltaEnum.HOUR_1:
        return timedelta(hours=1)
    elif td == TimedeltaEnum.DAY_1:
        return timedelta(days=1)
    elif td == TimedeltaEnum.DAY_30:
        return timedelta(days=30)
    else:
        raise NotImplementedError

@router.get('/ftx/spot-perp-pairs/ranked', tags=['ftx'])
async def list_ranked_spot_perp_pairs(funding_rate_1y_lower_bound: Optional[float] = 0):
    market_name_map = ftx_manager.market_name_map
    spot_base_currency_map = ftx_manager.spot_base_currency_map
    perp_underlying_map = ftx_manager.perp_underlying_map
    funding_rate_name_map = ftx_manager.funding_rate_name_map

    base_currencies = ftx_manager.list_spot_perp_base_currencies()
    pairs = [{
        'currency': spot_base_currency_map[currency]['baseCurrency'],
        'spot_name': spot_base_currency_map[currency]['name'],
        'spot_volume_usd_24h': spot_base_currency_map[currency]['volumeUsd24h'],
        'perp_name': perp_underlying_map[currency]['name'],
    } for currency in base_currencies]
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
    pairs = [pair for pair in pairs if pair['funding_rate_1y'] > funding_rate_1y_lower_bound]
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

@router.get('/ftx/risk-index', tags=['ftx'])
async def get_risk_index(api_client=Depends(get_current_ftx_rest_api_client)):
    risk_index = ftx_manager.get_risk_index(rest_api_client=api_client)
    return risk_index

@router.get('/ftx/funding-payments', tags=['ftx'])
async def list_funding_payments(td: TimedeltaEnum = None, api_client=Depends(get_current_ftx_rest_api_client)):
    if td:
        funding_payments = api_client.list_funding_payments(
            start_time=datetime.now() - to_td(td), end_time=datetime.now())
    else:
        funding_payments = api_client.list_funding_payments()
    return funding_payments

@router.get('/ftx/borrow-histories/spot-margin', tags=['ftx'])
async def list_spot_margin_borrow_histories(td: TimedeltaEnum = None, api_client=Depends(get_current_ftx_rest_api_client)):
    if td:
        spot_margin_borrow_histories = api_client.list_spot_margin_borrow_histories(
            start_time=datetime.now() - to_td(td), end_time=datetime.now())
    else:
        spot_margin_borrow_histories = api_client.list_spot_margin_borrow_histories()
    return spot_margin_borrow_histories

@router.get('/ftx/performance-report', tags=['ftx'])
async def get_performance_report(td: TimedeltaEnum = None, api_client=Depends(get_current_ftx_rest_api_client)):
    if td:
        funding_payments = api_client.list_funding_payments(
            start_time=datetime.now() - to_td(td), end_time=datetime.now())
        borrow_histories = api_client.list_spot_margin_borrow_histories(
            start_time=datetime.now() - to_td(td), end_time=datetime.now())
    else:
        funding_payments = api_client.list_funding_payments()
        borrow_histories = api_client.list_spot_margin_borrow_histories()

    funding_payment_time_map = defaultdict(float)
    if td in [TimedeltaEnum.HOUR_1, TimedeltaEnum.DAY_1]:
        for fp in funding_payments:
            funding_payment_time_map[fp['time']] += -fp['payment']
    else:
        for fp in funding_payments:
            funding_payment_time_map[fp['time'][:10]] += -fp['payment']

    borrow_history_coin_map = {}
    for bh in borrow_histories:
        coin = bh['coin']
        if not borrow_history_coin_map.get(coin):
            borrow_history_coin_map[coin] = { '_accumulated_size': 0, 'cost': 0 }
        borrow_history_coin_map[coin]['_accumulated_size'] += bh['size']
        borrow_history_coin_map[coin]['cost'] += bh['cost']
    for m in borrow_history_coin_map.values():
        m['avg_rate_1h'] = m['cost'] / m['_accumulated_size']
        m['avg_rate_1y'] = m['avg_rate_1h'] * 24 * 365
        del m['_accumulated_size']

    total_funding_payment_amount = sum(funding_payment_time_map.values())
    total_usd_like_borrow_cost_amount = sum(m['cost'] for coin, m in borrow_history_coin_map.items() if coin in ['USD', 'USDT'])
    return {
        'overview': {
            'total_funding_payment_amount': total_funding_payment_amount,
            'total_usd_like_borrow_cost_amount': total_usd_like_borrow_cost_amount,
            'total_usd_rough_profit': total_funding_payment_amount - total_usd_like_borrow_cost_amount,
        },
        'breakdown': {
            'funding_payment': funding_payment_time_map,
            'borrow_history': borrow_history_coin_map,
        },
    }

@router.post('/ftx/orders/spot-perp/{base_currency}', tags=['ftx'])
async def create_spot_perp_order(base_currency:str,
                                 base_amount:Optional[str]=None,
                                 quote_currency:Optional[ftx_manager.QuoteCurrencyEnum]=ftx_manager.QuoteCurrencyEnum.USD,
                                 quote_amount:Optional[str]=None,
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

@router.delete('/ftx/orders/spot-perp/{base_currency}', tags=['ftx'])
async def create_spot_perp_cancellation_order(base_currency:str,
                                              base_amount:Optional[str]=None,
                                              quote_currency:Optional[ftx_manager.QuoteCurrencyEnum]=ftx_manager.QuoteCurrencyEnum.USD,
                                              quote_amount:Optional[str]=None,
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
                                                                         rest_api_client=api_client,
                                                                         reverse_side=True)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return {
        'spot_order': spot_order,
        'perp_order': perp_order,
    }

@router.post('/ftx/orders/spot-perp/{base_currency}/balance', tags=['ftx'])
async def create_spot_perp_balancing_order(base_currency:str,
                                           quote_currency:Optional[ftx_manager.QuoteCurrencyEnum]=ftx_manager.QuoteCurrencyEnum.USD,
                                           api_client=Depends(get_current_ftx_rest_api_client)):
    try:
        perp_order = ftx_manager.place_spot_perp_balancing_order(base_currency,
                                                                 quote_currency=quote_currency,
                                                                 rest_api_client=api_client)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return perp_order

@router.post('/ftx/strategies/spot-futures-arbitrage/apply-iteration', tags=['ftx'])
async def apply_spot_futures_arbitrage_strategy_iteration(leverage_low: float = 11,
                                           leverage_high: float = 13,
                                           api_client=Depends(get_current_ftx_rest_api_client)):
    try:
        await ftx_manager.apply_spot_futures_arbitrage_strategy_iteration(
            leverage_low, leverage_high, rest_api_client=api_client)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return

@router.get('/ftx/strategies/spot-futures-arbitrage/config', tags=['ftx'])
async def get_spot_futures_arbitrage_strategy_config():
    return ftx_manager.get_config()

@router.patch('/ftx/strategies/spot-futures-arbitrage/config', tags=['ftx'])
async def config_spot_futures_arbitrage_strategy(config=Depends(ftx_manager.update_config)):
    return config
