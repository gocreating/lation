import statistics

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from lation.modules.coin.dependencies import get_current_ftx_rest_api_client
from lation.modules.coin.ftx import FTXManager, ftx_manager


router = APIRouter()


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

@router.get('/ftx/account/leverage', tags=['ftx'])
async def get_account_leverage(api_client=Depends(get_current_ftx_rest_api_client)):
    leverage = ftx_manager.get_leverage(rest_api_client=api_client)
    return leverage

@router.get('/ftx/funding-payments/30d', tags=['ftx'])
async def list_funding_payments(api_client=Depends(get_current_ftx_rest_api_client)):
    funding_payments_30d = api_client.list_funding_payments(start_time=datetime.now() - timedelta(days=30),
                                                            end_time=datetime.now())
    return funding_payments_30d

@router.get('/ftx/spot-margin/borrow-histories/30d', tags=['ftx'])
async def list_spot_margin_borrow_histories(api_client=Depends(get_current_ftx_rest_api_client)):
    spot_margin_borrow_histories_30d = api_client.list_spot_margin_borrow_histories(start_time=datetime.now() - timedelta(days=30),
                                                                                    end_time=datetime.now())
    return spot_margin_borrow_histories_30d

@router.get('/ftx/summary', tags=['ftx'])
async def get_summary(api_client=Depends(get_current_ftx_rest_api_client)):
    leverage = ftx_manager.get_leverage(rest_api_client=api_client)
    funding_payments_30d = api_client.list_funding_payments(start_time=datetime.now() - timedelta(days=30),
                                                            end_time=datetime.now())
    borrow_histories_30d = api_client.list_spot_margin_borrow_histories(start_time=datetime.now() - timedelta(days=30),
                                                                        end_time=datetime.now())
    future_names = set([p['future'] for p in funding_payments_30d])
    spot_names = set([b['coin'] for b in borrow_histories_30d])
    future_funding_payment_30d_map = {
        future_name: {
            # 'record_count': len([p for p in funding_payments_30d if p['future'] == future_name]),
            'time_period': {
                'start': min([p['time'] for p in funding_payments_30d if p['future'] == future_name]),
                'end': max([p['time'] for p in funding_payments_30d if p['future'] == future_name]),
            },
            'mean_funding_rate_1h': statistics.mean([p['rate'] for p in funding_payments_30d if p['future'] == future_name]),
            'mean_funding_rate_30d': statistics.mean([p['rate'] for p in funding_payments_30d if p['future'] == future_name]) * 24 * 30,
            'mean_funding_rate_1y': statistics.mean([p['rate'] for p in funding_payments_30d if p['future'] == future_name]) * 24 * 365,
            'total_usd_amount': -sum([p['payment'] for p in funding_payments_30d if p['future'] == future_name]),
        }
        for future_name in future_names
    }
    spot_borrow_history_30d_map = {
        spot_name: {
            'time_period': {
                'start': min([b['time'] for b in borrow_histories_30d if b['coin'] == spot_name]),
                'end': max([b['time'] for b in borrow_histories_30d if b['coin'] == spot_name]),
            },
            'mean_borrow_rate_1h': statistics.mean([b['rate'] for b in borrow_histories_30d if b['coin'] == spot_name]),
            'mean_borrow_rate_30d': statistics.mean([b['rate'] for b in borrow_histories_30d if b['coin'] == spot_name]) * 24 * 30,
            'mean_borrow_rate_1y': statistics.mean([b['rate'] for b in borrow_histories_30d if b['coin'] == spot_name]) * 24 * 365,
            'total_cost_amount': sum([b['cost'] for b in borrow_histories_30d if b['coin'] == spot_name]),
        }
        for spot_name in spot_names
    }
    return {
        'leverage': leverage,
        'funding_payment_30d': future_funding_payment_30d_map,
        'borrow_history_30d': spot_borrow_history_30d_map,
        'total_funding_payment_usd_amount': sum([p['total_usd_amount'] for p in future_funding_payment_30d_map.values()]),
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
