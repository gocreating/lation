import time

from lation.modules.base.models.end_user import EndUser
from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient, get_default_bitfinex_funding_strategy
from lation.modules.coin.routers.schemas import BitfinexFundingStrategy


def apply_bitfinex_funding_strategy(self, ask_rate:float):
    config = self.end_user_bitfinex_config
    if not config:
        return
    api_key = config.api_key
    api_secret = config.api_secret
    strategy = BitfinexFundingStrategy(**config.funding_strategy)
    if not api_key or not api_secret or not strategy:
        return
    if not strategy.enabled:
        return

    api_client = BitfinexAPIClient(api_key=api_key, api_secret=api_secret)
    wallets = api_client.get_user_wallets()
    for currency in ['USD']:
        symbol = f'f{currency}'
        symbol_strategy = strategy.symbol_strategy.get(symbol, None)
        if not symbol_strategy:
            continue
        if not symbol_strategy.enabled:
            continue

        # cancel offers
        funding_offers = api_client.get_user_funding_offers(symbol)
        for offer in funding_offers:
            cancel_funding_offer = api_client.cancel_user_funding_offer(offer.id)
            time.sleep(0.2)
        time.sleep(5)

        # submit offers
        amount_strategy = symbol_strategy.amount_strategy
        rate_strategy = symbol_strategy.rate_strategy
        rate_to_period_rules = symbol_strategy.rate_to_period_rules

        funding_wallet = next(wallet for wallet in wallets
                              if wallet.wallet_type == 'funding' and wallet.currency == currency)
        if not funding_wallet:
            continue
        available_balance = funding_wallet.available_balance - amount_strategy.hold_amount
        while available_balance >= amount_strategy.min_per_offer_amount:
            offer_amount = min(available_balance, amount_strategy.max_per_offer_amount)
            available_balance -= offer_amount
            offer_rate = max(ask_rate, rate_strategy.min_per_offer_rate / 36500)
            offer_period = 2
            for rule in rate_to_period_rules:
                if rule.gte_rate / 36500 <= offer_rate <= rule.lt_rate / 36500:
                    offer_period = rule.period
                    break
            submit_funding_offer = api_client.submit_user_funding_offer(BitfinexAPIClient.FundingOfferTypeEnum.LIMIT, symbol, f'{offer_amount}', f'{offer_rate}', offer_period)
            time.sleep(0.2)

EndUser.apply_bitfinex_funding_strategy = apply_bitfinex_funding_strategy
