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

@router.get('/ftx/summary', tags=['ftx'])
async def get_summary(strategy=Depends(get_current_ftx_spot_futures_arbitrage_strategy)):
    api_client = strategy.rest_api_client
    now = datetime.utcnow()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_yesterday = start_of_today - timedelta(days=1)
    start_of_last_7_day = start_of_today - timedelta(days=7)
    end_of_today = start_of_today + timedelta(days=1)
    end_of_yesterday = start_of_today

    min_start_time = start_of_last_7_day
    max_end_time = end_of_today

    funding_payments = api_client.list_funding_payments(start_time=min_start_time, end_time=max_end_time)
    borrow_histories = api_client.list_spot_margin_borrow_histories(start_time=min_start_time, end_time=max_end_time)

    def get_sub_summary(start_time: datetime, end_time: datetime, borrow_breakdown_ignore_lt_amount: float = 0.001) -> dict:
        # funding payment
        fp_count = 0
        accumulated_fp_amount = 0
        accumulated_fp_rate = 0
        filtered_funding_payments = [
            fp for fp in funding_payments
            if start_time <= datetime.fromisoformat(fp['time']).replace(tzinfo=None) < end_time
        ]
        for fp in filtered_funding_payments:
            accumulated_fp_amount += -fp['payment']
            accumulated_fp_rate += fp['rate']
            fp_count += 1
        avg_fp_rate_1h = accumulated_fp_rate / fp_count

        funding_payment_time_map = defaultdict(float)
        if end_time - start_time <= timedelta(days=1):
            for fp in filtered_funding_payments:
                funding_payment_time_map[fp['time']] += -fp['payment']
        else:
            for fp in filtered_funding_payments:
                funding_payment_time_map[fp['time'][:10]] += -fp['payment']

        # borrow history
        borrow_history_coin_map = {}
        for bh in borrow_histories:
            t = datetime.fromisoformat(bh['time']).replace(tzinfo=None)
            if start_time <= t < end_time:
                coin = bh['coin']
                if not borrow_history_coin_map.get(coin):
                    borrow_history_coin_map[coin] = { '_accumulated_size': 0, 'cost': 0 }
                borrow_history_coin_map[coin]['_accumulated_size'] += bh['size']
                borrow_history_coin_map[coin]['cost'] += bh['cost']
        for m in borrow_history_coin_map.values():
            avg_bh_rate_1h = m['cost'] / m['_accumulated_size']
            m['avg_rate_1y'] = f'{avg_bh_rate_1h * 100 * 24 * 365:.1f}%'
            m['avg_rate_1h'] = f'{avg_bh_rate_1h * 100:.6f}%'
            del m['_accumulated_size']
        total_usd_like_borrow_cost_amount = sum(m['cost'] for coin, m in borrow_history_coin_map.items() if coin in ['USD', 'USDT'])
        filtered_borrow_history_coin_map = {k: v for k, v in borrow_history_coin_map.items() if v['cost'] >= borrow_breakdown_ignore_lt_amount}
        for m in filtered_borrow_history_coin_map.values():
            m['cost'] = f"{m['cost']:.2f}"

        return {
            'datetime_range': f'{start_time} to {end_time}',
            'total_profit': f'~ {accumulated_fp_amount - total_usd_like_borrow_cost_amount:.2f} USD',
            'total_funding_payment_amount': f'{accumulated_fp_amount:.2f} USD',
            'total_usd_like_borrow_cost_amount': f'~ {total_usd_like_borrow_cost_amount:.2f} USD',
            'funding_payment': {
                'avg_rate_1y': f'{avg_fp_rate_1h * 100 * 24 * 365:.1f}%',
                'avg_rate_1h': f'{avg_fp_rate_1h * 100:.6f}%',
                'breakdown_by_time': funding_payment_time_map,
            },
            'borrow_breakdown': filtered_borrow_history_coin_map,
        }

    return {
        'current_leverage': f'{strategy.get_current_leverage():.1f}x',
        'today': get_sub_summary(start_of_today, end_of_today),
        'yesterday': get_sub_summary(start_of_yesterday, end_of_yesterday),
        'last_7_day': get_sub_summary(start_of_last_7_day, start_of_today),
    }
