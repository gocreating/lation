from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser
from lation.modules.base.models.job import CoroutineScheduler, JobProducer, Scheduler
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient
from lation.modules.coin.models.config import EndUserBitfinexConfig


bitfinex_funding_market_recommended_ask_rate = 2555
bitfinex_api_client = BitfinexAPIClient()

def get_bitfinex_funding_market_recommended_ask_rate() -> float:
    global bitfinex_funding_market_recommended_ask_rate
    return bitfinex_funding_market_recommended_ask_rate

@CoroutineScheduler.register_interval_job(10)
async def calculate_recommended_funding_rate(get_session):
    global bitfinex_funding_market_recommended_ask_rate
    book = bitfinex_api_client.get_book('fUSD', 'P0', 25)
    bitfinex_funding_market_recommended_ask_rate = (book['sell']['rate'][0] + book['buy']['rate'][-1]) * 0.5

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
