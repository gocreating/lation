from decimal import Decimal

from lation.modules.base.models.job import CoroutineScheduler
from lation.modules.base_fastapi.line_api_client import LineAPIClient
from lation.modules.spot_perp_bot.env import \
    FTX_API_KEY_ROOT, FTX_API_SECRET_ROOT, \
    FTX_API_KEY_ME, FTX_API_SECRET_ME, \
    FTX_API_KEY_MOM, FTX_API_SECRET_MOM, \
    FTX_API_KEY_SISTER, FTX_API_SECRET_SISTER
from lation.modules.spot_perp_bot.ftx import FTXRestAPIClient, FTXSpotFuturesArbitrageStrategy
from lation.modules.spot_perp_bot.schemas import FtxArbitrageStrategyConfig


ftx_spot_futures_arbitrage_strategies = []

default_strategy_config = FtxArbitrageStrategyConfig(
    alarm=FtxArbitrageStrategyConfig.AlarmConfig(),
    increase_pair=FtxArbitrageStrategyConfig.IncreasePairConfig(
        leverage_diff_to_quote_amount_rules=[
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=1, lt_leverage_diff=2, quote_amount=Decimal('20')),
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=2, lt_leverage_diff=20, quote_amount=Decimal('50')),
        ]
    ),
    always_increase_pair=FtxArbitrageStrategyConfig.AlwaysIncreasePairConfig(),
    decrease_pair=FtxArbitrageStrategyConfig.DecreasePairConfig(
        leverage_diff_to_quote_amount_rules=[
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=1, lt_leverage_diff=2, quote_amount=Decimal('20')),
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=2, lt_leverage_diff=20, quote_amount=Decimal('50')),
        ]
    ),
    always_decrease_pair=FtxArbitrageStrategyConfig.AlwaysDecreasePairConfig(),
    close_pair=FtxArbitrageStrategyConfig.ClosePairConfig(),
    garbage_collect=FtxArbitrageStrategyConfig.GarbageCollectConfig()
)

if FTX_API_KEY_ROOT and FTX_API_SECRET_ROOT:
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_ROOT,
                             api_secret=FTX_API_SECRET_ROOT,
                             subaccount_name=None),
            default_strategy_config))

if FTX_API_KEY_ME and FTX_API_SECRET_ME:
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_ME,
                             api_secret=FTX_API_SECRET_ME,
                             subaccount_name='期现套利子帳戶'),
            default_strategy_config))

if FTX_API_KEY_MOM and FTX_API_SECRET_MOM:
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_MOM,
                             api_secret=FTX_API_SECRET_MOM,
                             subaccount_name='媽媽'),
            default_strategy_config))

if FTX_API_KEY_SISTER and FTX_API_SECRET_SISTER:
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_SISTER,
                             api_secret=FTX_API_SECRET_SISTER,
                             subaccount_name='姊姊'),
            default_strategy_config))


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
