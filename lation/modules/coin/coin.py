from lation.modules.customer.customer import CustomerApp
from lation.modules.coin.routers import bitfinex


class CoinFastApp(CustomerApp):

    def __init__(self):
        super().__init__()
        self.include_router(bitfinex.router)
