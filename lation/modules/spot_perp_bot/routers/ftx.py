import enum
from collections import defaultdict

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from lation.modules.spot_perp_bot.dependencies import get_current_ftx_spot_futures_arbitrage_strategy


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
async def config_spot_futures_arbitrage_strategy(strategy=Depends(get_current_ftx_spot_futures_arbitrage_strategy),
                                                 alarm_enabled: bool = None,
                                                 leverage_alarm: float = None,
                                                 strategy_enabled: bool = None,
                                                 leverage_low: float = None,
                                                 leverage_high: float = None,
                                                 leverage_close: float = None,
                                                 garbage_collection_enabled: bool = None):
    config = strategy.get_config()
    leverage_low = leverage_low or config['leverage_low']
    leverage_high = leverage_high or config['leverage_high']
    leverage_close = leverage_close or config['leverage_close']
    if leverage_low and leverage_high:
        assert leverage_low < leverage_high
    if leverage_high and leverage_close:
        assert leverage_high < leverage_close
    config = strategy.update_config(alarm_enabled=alarm_enabled,
                                    leverage_alarm=leverage_alarm,
                                    strategy_enabled=strategy_enabled,
                                    leverage_low=leverage_low,
                                    leverage_high=leverage_high,
                                    leverage_close=leverage_close,
                                    garbage_collection_enabled=garbage_collection_enabled)
    return config

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
