import statistics
from decimal import Decimal

from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser
from lation.modules.base.models.job import CoroutineScheduler, JobProducer, Scheduler
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient
from lation.modules.coin.dependencies import get_current_ftx_rest_api_client
from lation.modules.coin.ftx import ftx_manager
from lation.modules.coin.models.config import EndUserBitfinexConfig
from lation.modules.customer.models.oauth_user import LineUser


##############
## Bitfinex ##
##############

bitfinex_funding_market_recommended_ask_rates = [25.55 for _ in range(12)]
bitfinex_api_client = BitfinexAPIClient()

def get_bitfinex_funding_market_recommended_ask_rate() -> float:
    global bitfinex_funding_market_recommended_ask_rates
    return statistics.mean(bitfinex_funding_market_recommended_ask_rates)

def arg_max_ask_amount(book):
    max_ask_amount_index = 0
    max_ask_amount = book['ask']['amount'][max_ask_amount_index]
    for i, amount in enumerate(book['ask']['amount']):
        if amount > max_ask_amount:
            max_ask_amount_index, max_ask_amount = i, amount
    return max_ask_amount_index

@CoroutineScheduler.register_interval_job(10)
async def calculate_recommended_funding_rate(get_session):
    global bitfinex_funding_market_recommended_ask_rates
    book_r0 = bitfinex_api_client.get_book('fUSD', 'R0', 100)
    book_p1 = bitfinex_api_client.get_book('fUSD', 'P1', 100)
    i_r0 = max(0, arg_max_ask_amount(book_r0) - 1)
    i_p1 = max(0, arg_max_ask_amount(book_p1) - 1)
    best_ask_rate = max(book_r0['ask']['rate'][i_r0], book_r0['ask']['rate'][i_p1])
    bitfinex_funding_market_recommended_ask_rates.append(best_ask_rate)
    bitfinex_funding_market_recommended_ask_rates.pop(0)

@Scheduler.register_cron_job()
def apply_bitfinex_funding_strategy(cron_job) -> str:
    session = object_session(cron_job)
    end_users = session.query(EndUser)\
        .join(EndUser.end_user_bitfinex_config)\
        .filter(EndUserBitfinexConfig.api_key != None,
                EndUserBitfinexConfig.api_secret != None,
                EndUserBitfinexConfig.funding_strategy != None)\
        .all()
    ask_rate = get_bitfinex_funding_market_recommended_ask_rate()
    for end_user in end_users:
        if end_user.is_subscribed_to_any_products(['CFB']):
            JobProducer(end_user).apply_bitfinex_funding_strategy(ask_rate)

    end_user_ids = [end_user.id for end_user in end_users]
    return f'ask_rate={ask_rate}, end_user_ids={end_user_ids}'


#########
## FTX ##
#########

@CoroutineScheduler.register_interval_job(600)
async def fetch_ftx_market(get_session):
    ftx_manager.update_market_state()

@CoroutineScheduler.register_interval_job(30)
async def fetch_ftx_funding_rate(get_session):
    ftx_manager.update_funding_rate_state()

@CoroutineScheduler.register_interval_job(120)
async def experiment_my_ftx_leverage_alarm(get_session):
    messages = []
    for subaccount_name in [None, '期现套利子帳戶']:
        api_client = await get_current_ftx_rest_api_client(subaccount_name=subaccount_name)
        risk_index = ftx_manager.get_risk_index(rest_api_client=api_client)
        current_leverage = risk_index['leverage']['current']
        if current_leverage > 14:
            account_name = subaccount_name
            if not account_name:
                account_name = '主帳戶'
            quantized_current_leverage = Decimal(current_leverage).quantize(Decimal('.00'))
            messages.append({
                'type': 'text',
                'text': f'您的 FTX「{account_name}」目前槓桿 {quantized_current_leverage} 倍',
            })
    if not messages:
        return

    session = get_session()
    my_line_user = session.query(LineUser)\
        .filter(LineUser.account_identifier == 'U5abfe9090acd8357516e26604a3606b6')\
        .one_or_none()
    if not my_line_user:
        return

    my_line_user.push_message(messages)

@CoroutineScheduler.register_interval_job(5)
async def experiment_my_ftx_leverage_alarm(get_session):
    if not ftx_manager.strategy_enabled:
        return
    messages = []
    for subaccount_name in [None, '期现套利子帳戶']:
        try:
            api_client = await get_current_ftx_rest_api_client(subaccount_name=subaccount_name)
            await ftx_manager.apply_spot_futures_arbitrage_strategy_iteration(ftx_manager.leverage_low, ftx_manager.leverage_high, rest_api_client=api_client)
        except Exception as e:
            messages.append({
                'type': 'text',
                'text': f'您的 FTX「{account_name}」執行策略時發生錯誤：',
            })
            messages.append({
                'type': 'text',
                'text': str(e),
            })

    if not messages:
        return
    session = get_session()
    my_line_user = session.query(LineUser)\
        .filter(LineUser.account_identifier == 'U5abfe9090acd8357516e26604a3606b6')\
        .one_or_none()
    if not my_line_user:
        return

    my_line_user.push_message(messages)

