from lation.modules.base.models.end_user import EndUser


def apply_bitfinex_funding_strategy(self, ask_rate:float):
    print(ask_rate)

EndUser.apply_bitfinex_funding_strategy = apply_bitfinex_funding_strategy
