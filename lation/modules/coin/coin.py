from lation.modules.customer.customer import CustomerApp
from lation.modules.coin.routers import bitfinex, experiment, user


class CoinFastApp(CustomerApp):

    def __init__(self):
        super().__init__()
        self.include_router(user.router)
        self.include_router(bitfinex.router)
        self.include_router(experiment.router)
