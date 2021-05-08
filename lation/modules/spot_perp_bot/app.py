import enum
from decimal import Decimal

from lation.core.module import load_modules
from lation.modules.spot_perp_bot.env import \
    FTX_API_KEY_ROOT, FTX_API_SECRET_ROOT, \
    FTX_API_KEY_ME, FTX_API_SECRET_ME, \
    FTX_API_KEY_MOM, FTX_API_SECRET_MOM, \
    FTX_API_KEY_SISTER, FTX_API_SECRET_SISTER
from lation.modules.spot_perp_bot.ftx import FTXRestAPIClient, FTXSpotFuturesArbitrageStrategy
from lation.modules.spot_perp_bot.schemas import FtxArbitrageStrategyConfig
from lation.modules.spot_perp_bot.spot_perp_bot import SpotPerpBotApp


load_modules()

ftx_spot_futures_arbitrage_strategies = []

default_strategy_config = FtxArbitrageStrategyConfig(
    alarm=FtxArbitrageStrategyConfig.AlarmConfig(),
    increase_pair=FtxArbitrageStrategyConfig.IncreasePairConfig(
        leverage_diff_to_quote_amount_rules=[
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=1, lt_leverage_diff=2, quote_amount=Decimal('20')),
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=2, lt_leverage_diff=20, quote_amount=Decimal('50')),
        ]
    ),
    decrease_pair=FtxArbitrageStrategyConfig.DecreasePairConfig(
        leverage_diff_to_quote_amount_rules=[
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=1, lt_leverage_diff=2, quote_amount=Decimal('20')),
            FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule(gte_leverage_diff=2, lt_leverage_diff=20, quote_amount=Decimal('50')),
        ]
    ),
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

app = SpotPerpBotApp()
