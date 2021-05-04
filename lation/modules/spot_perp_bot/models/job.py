from decimal import Decimal

from lation.modules.base.models.job import CoroutineScheduler
from lation.modules.base_fastapi.line_api_client import LineAPIClient
from lation.modules.spot_perp_bot.routers.schemas import ftx_spot_futures_arbitrage_strategies


#########
## FTX ##
#########

@CoroutineScheduler.register_interval_job(15)
async def execute_ftx_spot_futures_arbitrage_strategies(get_session):
    for strategy in ftx_spot_futures_arbitrage_strategies:
        await strategy.execute()

@CoroutineScheduler.register_interval_job(15)
async def execute_ftx_spot_futures_arbitrage_strategy_garbage_collections(get_session):
    for strategy in ftx_spot_futures_arbitrage_strategies:
        await strategy.decrease_negative_funding_payment_pairs()

@CoroutineScheduler.register_interval_job(120)
async def ftx_spot_futures_arbitrage_strategy_alarms(get_session):
    messages = []
    for strategy in ftx_spot_futures_arbitrage_strategies:
        should_raise_alarm, current_leverage = strategy.should_raise_leverage_alarm()
        if not should_raise_alarm:
            continue
        account_name = strategy.rest_api_client.subaccount_name
        if not account_name:
            account_name = '主帳戶'
        quantized_current_leverage = Decimal(current_leverage).quantize(Decimal('.00'))
        messages.append({
            'type': 'text',
            'text': f'您的 FTX (子)帳戶「{account_name}」目前槓桿 {quantized_current_leverage} 倍',
        })
    if not messages:
        return

    line_api_client = LineAPIClient()
    line_api_client.push_message('U5abfe9090acd8357516e26604a3606b6', messages)
