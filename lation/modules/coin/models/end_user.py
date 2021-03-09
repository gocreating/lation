from lation.modules.base.models.end_user import EndUser
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient, get_default_bitfinex_funding_strategy


def apply_bitfinex_funding_strategy(self, ask_rate:float):
    config = self.end_user_bitfinex_config
    if not config:
        return
    api_key = config.api_key
    api_secret = config.api_secret
    strategy = config.funding_strategy
    if not api_key or not api_secret or not strategy:
        return
    api_client = BitfinexAPIClient(api_key=api_key, api_secret=api_secret)
    wallets = api_client.get_user_wallets()
    funding_wallet = next(wallet for wallet in wallets if wallet.wallet_type == 'funding')
    print(ask_rate, funding_wallet.available_balance)

EndUser.apply_bitfinex_funding_strategy = apply_bitfinex_funding_strategy
