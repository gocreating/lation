import statistics

from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser
from lation.modules.base.models.job import CoroutineScheduler, JobProducer, Scheduler
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient
from lation.modules.coin.models.config import EndUserBitfinexConfig


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
        JobProducer(end_user).apply_bitfinex_funding_strategy(ask_rate)

    end_user_ids = [end_user.id for end_user in end_users]
    return f'ask_rate={ask_rate}, end_user_ids={end_user_ids}'
