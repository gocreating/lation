import enum

from lation.core.env import get_env
from lation.core.utils import extend_enum
from lation.modules.spot_perp_bot.ftx import FTXRestAPIClient, FTXSpotFuturesArbitrageStrategy


FTX_API_KEY_ROOT = get_env('FTX_API_KEY_ROOT')
FTX_API_SECRET_ROOT = get_env('FTX_API_SECRET_ROOT')

FTX_API_KEY_ME = get_env('FTX_API_KEY_ME')
FTX_API_SECRET_ME = get_env('FTX_API_SECRET_ME')

FTX_API_KEY_MOM = get_env('FTX_API_KEY_MOM')
FTX_API_SECRET_MOM = get_env('FTX_API_SECRET_MOM')

FTX_API_KEY_SISTER = get_env('FTX_API_KEY_SISTER')
FTX_API_SECRET_SISTER = get_env('FTX_API_SECRET_SISTER')

ftx_spot_futures_arbitrage_strategies = []

class SubaccountNameEnum(enum.Enum):
    pass

if FTX_API_KEY_ROOT and FTX_API_SECRET_ROOT:
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_ROOT, api_secret=FTX_API_SECRET_ROOT, subaccount_name=None),
            strategy_enabled=False, garbage_collection_enabled=False))

if FTX_API_KEY_ME and FTX_API_SECRET_ME:
    class SubaccountNameEnumMe(enum.Enum):
        我 = '期现套利子帳戶'
    SubaccountNameEnum = extend_enum(SubaccountNameEnum, SubaccountNameEnumMe)
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_ME, api_secret=FTX_API_SECRET_ME, subaccount_name='期现套利子帳戶'),
            strategy_enabled=False, garbage_collection_enabled=False))

if FTX_API_KEY_MOM and FTX_API_SECRET_MOM:
    class SubaccountNameEnumMom(enum.Enum):
        媽媽 = '媽媽'
    SubaccountNameEnum = extend_enum(SubaccountNameEnum, SubaccountNameEnumMom)
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_MOM, api_secret=FTX_API_SECRET_MOM, subaccount_name='媽媽'),
            strategy_enabled=False, garbage_collection_enabled=False))

if FTX_API_KEY_SISTER and FTX_API_SECRET_SISTER:
    class SubaccountNameEnumSister(enum.Enum):
        姊姊 = '姊姊'
    SubaccountNameEnum = extend_enum(SubaccountNameEnum, SubaccountNameEnumSister)
    ftx_spot_futures_arbitrage_strategies.append(
        FTXSpotFuturesArbitrageStrategy(
            FTXRestAPIClient(api_key=FTX_API_KEY_SISTER, api_secret=FTX_API_SECRET_SISTER, subaccount_name='姊姊'),
            strategy_enabled=False, garbage_collection_enabled=False))
