import enum
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from lation.modules.spot_perp_bot.dependencies import get_current_ftx_spot_futures_arbitrage_strategy
from lation.modules.spot_perp_bot.schemas import FtxArbitrageStrategyConfig


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


@router.get('/ftx/strategies/spot-futures-arbitrage/config', tags=['ftx'])
async def get_spot_futures_arbitrage_strategy_config(strategy=Depends(get_current_ftx_spot_futures_arbitrage_strategy)):
    return strategy.get_config()

@router.patch('/ftx/strategies/spot-futures-arbitrage/config', tags=['ftx'])
async def config_spot_futures_arbitrage_strategy(config: FtxArbitrageStrategyConfig,
                                                 strategy=Depends(get_current_ftx_spot_futures_arbitrage_strategy)):
    current_config = strategy.get_config()
    partial_config = config.dict(exclude_unset=True)
    new_config = strategy.update_config(partial_config)
    return new_config

@router.get('/ftx/leverage', tags=['ftx'])
async def get_leverage(strategy=Depends(get_current_ftx_spot_futures_arbitrage_strategy)):
    return {
        'current_leverage': strategy.get_current_leverage(),
    }

@router.get('/ftx/performance-report', tags=['ftx'])
async def get_performance_report(td: TimedeltaEnum = None, strategy=Depends(get_current_ftx_spot_futures_arbitrage_strategy)):
    api_client = strategy.rest_api_client
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
