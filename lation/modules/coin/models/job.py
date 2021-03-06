from lation.modules.base.models.job import CoroutineScheduler
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient


bitfinex_funding_market_recommended_ask_rate = 2555
bitfinex_api_client = BitfinexAPIClient()

def get_bitfinex_funding_market_recommended_ask_rate() -> float:
    global bitfinex_funding_market_recommended_ask_rate
    return bitfinex_funding_market_recommended_ask_rate

@CoroutineScheduler.register_interval_job(5)
async def calculate_recommended_funding_rate(get_session):
    global bitfinex_funding_market_recommended_ask_rate
    book = bitfinex_api_client.get_book('fUSD', 'P0', 25)
    bitfinex_funding_market_recommended_ask_rate = (book['sell']['rate'][0] + book['buy']['rate'][-1]) * 0.5
