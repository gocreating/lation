from lation.modules.base.models.job import CoroutineScheduler
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient


recommended_sell_rate = 2555
bitfinex_api_client = BitfinexAPIClient()

def get_funding_market_recommended_sell_rate() -> float:
    global recommended_sell_rate
    return recommended_sell_rate

@CoroutineScheduler.register_interval_job(5)
async def calculate_recommended_funding_rate():
    global recommended_sell_rate
    book = bitfinex_api_client.get_book('fUSD', 'P0', 25)
    recommended_sell_rate = (book['sell']['rate'][0] + book['buy']['rate'][-1]) * 0.5
