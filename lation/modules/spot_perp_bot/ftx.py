from __future__ import annotations
import asyncio
import enum
import hmac
import statistics
import time
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import ROUND_FLOOR, Decimal
from typing import Any, Dict, List, Optional, Tuple

from pydantic.utils import deep_update
from requests import Request, Session, Response

from lation.core.logger import create_logger
from lation.core.utils import RateLimiter
from lation.modules.spot_perp_bot.schemas import FtxArbitrageStrategyConfig


logger = create_logger()

class FTXSpotFuturesArbitrageStrategy():

    # https://help.ftx.com/hc/en-us/articles/360031149632-Non-USD-Collateral
    # NON_USD_COLLATERALS = ['1INCH', 'AAPL', 'AAVE', 'ABNB', 'ACB', 'ALPHA', 'AMC', 'AMD', 'AMZN', 'APHA', 'ARKK', 'AUD', 'BABA', 'BADGER', 'BAND', 'BAO', 'BB', 'BCH', 'BILI', 'BITW', 'BNB', 'BNT', 'BNTX', 'BRL', 'BRZ', 'BTC', 'BTMX', 'BUSD', 'BVOL', 'BYND', 'CAD', 'CBSE', 'CEL', 'CGC', 'CHF', 'CRON', 'CUSDT', 'DAI', 'DOGE', 'ETH', 'ETHE', 'EUR', 'FB', 'FIDA', 'FTM', 'FTT', 'GBP', 'GBTC', 'GDX', 'GDXJ', 'GLD', 'GLXY', 'GME', 'GOOGL', 'GRT', 'HKD', 'HOLY', 'HOOD', 'HT', 'HUSD', 'HXRO', 'IBVOL', 'KIN', 'KNC', 'LEND', 'LEO', 'LINK', 'LRC', 'LTC', 'MATIC', 'MKR', 'MOB', 'MRNA', 'MSTR', 'NFLX', 'NIO', 'NOK', 'NVDA', 'OKB', 'OMG', 'PAX', 'PAXG', 'PENN', 'PFE', 'PYPL', 'RAY', 'REN', 'RSR', 'RUNE', 'SECO', 'SGD', 'SLV', 'SNX', 'SOL', 'SPY', 'SQ', 'SRM', 'SUSHI', 'SXP', 'TLRY', 'TOMO', 'TRX', 'TRY', 'TRYB', 'TSLA', 'TSM', 'TUSD', 'TWTR', 'UBER', 'UNI', 'USD', 'USDC', 'USDT', 'USO', 'WBTC', 'WUSDC', 'XAUT', 'XRP', 'YFI', 'ZAR', 'ZM', 'ZRX']

    QUOTE_CURRENCIES = ['USD', 'USDT']
    black_list_coins = set([
        # usd-fungible coins
        'USD', 'TUSD', 'USDC', 'PAX', 'BUSD', 'HUSD', 'WUSDC',
        # fiat coins
        'USD', 'EUR', 'GBP', 'AUD', 'HKD', 'SGD', 'TRY', 'ZAR', 'CAD', 'CHF', 'BRL',
        # non-spot-margin coins
        'FTT', 'TUSD', 'USDC', 'PAX', 'BUSD', 'HUSD', 'HKD', 'SGD', 'TRY', 'ZAR', 'CHF', 'COMP', 'SRM', 'SOL', 'HXRO', 'WUSDC', 'FIDA', 'HOLY', 'SECO', 'BAO', 'BADGER', 'RAY', 'KIN', 'ZRX', 'FTM', 'LRC', 'WUSDT', 'COPE', 'BVOL', 'IBVOL',
        # custom selected coins
        'USDT',
    ])
    white_list_coins = set(['FTT'])

    pair_map = None
    last_spread_rate_update_time = None
    last_funding_rate_update_time = None

    class OrderDirection(str, enum.Enum):
        SPOT_LONG_PERP_SHORT = 'SPOT_LONG_PERP_SHORT'
        SPOT_SHORT_PERP_LONG = 'SPOT_SHORT_PERP_LONG'

    @staticmethod
    def get_pair_market(market_name_map: dict, base_currency: str, quote_currency: str) -> Tuple[dict, dict]:
        spot_market = market_name_map.get(f'{base_currency}/{quote_currency}')
        perp_market = market_name_map.get(f'{base_currency}-PERP')
        return spot_market, perp_market

    @staticmethod
    def get_quote_amount_from_rules(leverage_diff, leverage_diff_to_quote_amount_rules: List[FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule]) -> Optional[Decimal]:
        quote_amount = None
        for rule in leverage_diff_to_quote_amount_rules:
            if rule.gte_leverage_diff <= leverage_diff < rule.lt_leverage_diff:
                quote_amount = rule.quote_amount
                break
        return quote_amount

    def __init__(self, rest_api_client: FTXRestAPIClient, config: FtxArbitrageStrategyConfig):
        self.rest_api_client = rest_api_client
        self.config = config
        self.initialize_pair_map()
        # TODO: check margin funding is enabled

    def log(self, fn_name: str, msg: str, *args, **kwargs):
        getattr(logger, fn_name)(f'[FTX Strategy] [account={self.rest_api_client.subaccount_name}] {msg}', *args, **kwargs)

    def log_info(self, *args, **kwargs):
        self.log('info', *args, **kwargs)

    def log_error(self, *args, **kwargs):
        self.log('error', *args, **kwargs)

    def get_config(self) -> FtxArbitrageStrategyConfig:
        return self.config

    def update_config(self, partial_config: dict) -> FtxArbitrageStrategyConfig:
        self.config = FtxArbitrageStrategyConfig(**deep_update(self.config.dict(), partial_config))
        return self.get_config()

    def get_current_leverage(self) -> float:
        account_info = self.rest_api_client.get_account_info()
        current_mf = account_info['marginFraction']
        current_leverage = 0 if not current_mf else 1 / current_mf
        return current_leverage

    def get_market_name_map(self) -> dict:
        markets = self.rest_api_client.list_markets()
        market_name_map = {market['name']: market for market in markets}
        return market_name_map

    def get_coins(self) -> Tuple[set, set]:
        wallet_coins = self.rest_api_client.list_wallet_coins()
        collateral_coins = set([coin['id'] for coin in wallet_coins if coin['collateral']])
        return collateral_coins, (collateral_coins - self.black_list_coins).union(self.white_list_coins)

    def initialize_pair_map(self):
        cls = self.__class__
        market_name_map = self.get_market_name_map()
        all_coins, support_coins = self.get_coins()
        pair_map = {}
        for base_currency in all_coins:
            for quote_currency in self.QUOTE_CURRENCIES:
                spot_market, perp_market = FTXSpotFuturesArbitrageStrategy.get_pair_market(market_name_map, base_currency, quote_currency)
                if not spot_market or not perp_market:
                    continue
                pair_map[(base_currency, quote_currency)] = {
                    'is_valid': base_currency in support_coins,
                    'spot_market_name': spot_market['name'],
                    'perp_market_name': perp_market['name'],
                    'base_currency': base_currency,
                    'quote_currency': quote_currency,
                    'spot_size_increment': Decimal(str(spot_market['sizeIncrement'])),
                    'perp_size_increment': Decimal(str(perp_market['sizeIncrement'])),
                    'common_size_increment': Decimal(str(max(spot_market['sizeIncrement'], perp_market['sizeIncrement']))).normalize(),
                    'spot_min_provide_size': Decimal(str(spot_market['minProvideSize'])),
                    'perp_min_provide_size': Decimal(str(perp_market['minProvideSize'])),
                    'min_provide_size': Decimal(str(max(spot_market['minProvideSize'], perp_market['minProvideSize']))),
                }
        cls.pair_map = pair_map

    def should_update_spread_rate(self):
        # won't update spread within every 5 seconds
        cls = self.__class__
        utc_now = datetime.utcnow()
        return not cls.last_spread_rate_update_time or utc_now - cls.last_spread_rate_update_time >= timedelta(seconds=5)

    def update_spread_rate(self, market_name_map: dict):
        cls = self.__class__
        for base_currency, quote_currency in cls.pair_map:
            spot_market, perp_market = FTXSpotFuturesArbitrageStrategy.get_pair_market(market_name_map, base_currency, quote_currency)
            spot_price = (spot_market['bid'] + spot_market['ask']) / 2
            perp_price = (perp_market['bid'] + perp_market['ask']) / 2
            spread_rate = (perp_price - spot_price) / spot_price
            cls.pair_map[(base_currency, quote_currency)].update({
                'spot_price': spot_price,
                'perp_price': perp_price,
                'spread_rate': spread_rate,
            })
        cls.last_spread_rate_update_time = datetime.utcnow()

    def should_update_funding_rate(self):
        # won't update funding rate within the same hour
        cls = self.__class__
        utc_now = datetime.utcnow()
        return not cls.last_funding_rate_update_time or (
            utc_now.date() == cls.last_funding_rate_update_time.date() and
            utc_now.hour != cls.last_funding_rate_update_time.hour
        )

    def update_funding_rate(self, market_name_map: dict):
        cls = self.__class__
        funding_rates = self.rest_api_client.list_funding_rates(
            start_time=datetime.now() - timedelta(hours=6), end_time=datetime.now())
        funding_rates_map = defaultdict(list)
        for fr in funding_rates:
            funding_rates_map[fr['future']].append(fr['rate'])
        for base_currency, quote_currency in cls.pair_map:
            _, perp_market = FTXSpotFuturesArbitrageStrategy.get_pair_market(market_name_map, base_currency, quote_currency)
            funding_rates = funding_rates_map[perp_market['name']]
            cls.pair_map[(base_currency, quote_currency)].update({
                'funding_rate': statistics.mean(funding_rates),
            })
        cls.last_funding_rate_update_time = datetime.utcnow()

    def get_too_much_currencies(self, balance_map: dict) -> List[str]:
        # check each coin shares balanced percentage
        usd_value = balance_map['USD']['total']
        total_value = usd_value
        value_map = {
            'USD': usd_value,
        }
        for base_currency, balance in balance_map.items():
            for quote_currency in self.QUOTE_CURRENCIES:
                pair = self.pair_map.get((base_currency, quote_currency))
                if not pair:
                    continue
                spot_price = pair.get('spot_price')
                if not spot_price:
                    continue
                value = balance['total'] * spot_price
                value_map[base_currency] = value
                total_value += value
                break
        too_much_currencies = []
        for base_currency, value in value_map.items():
            if value / total_value > self.config.increase_pair.max_balance_rate:
                too_much_currencies.append(base_currency)
        return too_much_currencies

    def get_sorted_pairs_from_market(self, reverse=False) -> List[dict]:
        cls = self.__class__
        market_name_map = self.get_market_name_map()

        # won't update spread within every 5 seconds
        if self.should_update_spread_rate():
            self.update_spread_rate(market_name_map)

        # won't update funding rate within the same hour
        if self.should_update_funding_rate():
            self.update_funding_rate(market_name_map)

        # filter out risking pairs
        pair_map = {key: pair for key, pair in cls.pair_map.items()
                    if pair['is_valid'] and pair['spread_rate'] * pair['funding_rate'] > 0}
        pairs = pair_map.values()

        # sort by spread rate
        spread_rate_pairs = [pair for pair in sorted(pairs, key=lambda pair: abs(pair['spread_rate']), reverse=True)]
        for i, pair in enumerate(spread_rate_pairs):
            pair_map[(pair['base_currency'], pair['quote_currency'])].update({
                'spread_rate_rank': i,
            })

        # sort by funding rate
        funding_rate_pairs = [pair for pair in sorted(pairs, key=lambda pair: abs(pair['funding_rate']), reverse=True)]
        for i, pair in enumerate(funding_rate_pairs):
            pair_map[(pair['base_currency'], pair['quote_currency'])].update({
                'funding_rate_rank': i,
            })

        sorted_pairs = sorted(pair_map.values(), key=lambda pair: pair['spread_rate_rank'] + pair['funding_rate_rank'], reverse=reverse)
        return sorted_pairs

    def get_best_pair_from_market(self) -> dict:
        balance_map = self.get_balance_map()
        too_much_currencies = self.get_too_much_currencies(balance_map)
        sorted_pairs = self.get_sorted_pairs_from_market()
        if self.config.increase_pair.allow_spot_short_perp_long:
            return next(pair for pair in sorted_pairs if pair['base_currency'] not in too_much_currencies)
        else:
            return next(pair for pair in sorted_pairs if pair['base_currency'] not in too_much_currencies and pair['funding_rate'] > 0)

    def get_worst_pair_from_asset(self) -> Optional[dict]:
        sorted_pairs = self.get_sorted_pairs_from_market(reverse=True)
        balance_map, position_map = self.get_asset_map()
        for pair in sorted_pairs:
            balance = balance_map.get(pair['base_currency'])
            position = position_map.get(pair['perp_market_name'])
            if not balance or not position:
                continue
            if abs(balance['total']) < pair['min_provide_size'] or abs(position['net_size']) < pair['min_provide_size']:
                continue
            return pair, balance, position
        return None

    def get_balance_map(self) -> dict:
        balances = self.rest_api_client.list_wallet_balances()
        balance_map = {balance['coin']: {'total': balance['total']} for balance in balances if balance['total'] != 0}
        return balance_map

    def get_position_map(self) -> dict:
        positions = self.rest_api_client.list_positions()
        # netSize: Size of position. Positive if long, negative if short.
        position_map = {position['future']: {'net_size': position['netSize']} for position in positions if position['netSize'] != 0}
        return position_map

    def get_asset_map(self) -> Tuple[dict, dict]:
        return self.get_balance_map(), self.get_position_map()

    def get_imbalanced_pairs(self, balance_map: dict, position_map: dict) -> List[dict]:
        cls = self.__class__
        unique_base_currencies = set(['USD', 'USDT'])
        imbalanced_pairs = []
        for pair in cls.pair_map.values():
            if pair['base_currency'] in unique_base_currencies:
                continue
            unique_base_currencies.add(pair['base_currency'])
            balance = balance_map.get(pair['base_currency'])
            position = position_map.get(pair['perp_market_name'])
            if not balance and not position:
                continue
            if (balance and not position) or (not balance and position):
                imbalanced_pairs.append(pair)
                continue
            if abs(abs(balance['total']) - abs(position['net_size'])) < pair['min_provide_size']:
                continue
            imbalanced_pairs.append(pair)
        return imbalanced_pairs

    async def make_pair(self, pair: dict, amount: Decimal, order_direction: OrderDirection) -> Tuple[dict, dict]:
        cls = self.__class__
        order_size = float(amount.quantize(pair['common_size_increment'], rounding=ROUND_FLOOR))
        if order_size < pair['min_provide_size']:
            raise Exception(f'`amount` is too small')
        order_price = None # Send null for market orders
        order_type = 'market' # "limit" or "market"
        ts = int(time.time() * 1000)
        client_id_spot = f'lation_coin_spot_order_{ts}'
        client_id_perp = f'lation_coin_perp_order_{ts}'

        loop = asyncio.get_running_loop()
        if order_direction == cls.OrderDirection.SPOT_LONG_PERP_SHORT:
            spot_order, perp_order = await asyncio.gather(
                loop.run_in_executor(None, lambda: self.rest_api_client.place_order(
                    pair['spot_market_name'], 'buy', order_price, order_size, type_=order_type, client_id=client_id_spot)),
                loop.run_in_executor(None, lambda: self.rest_api_client.place_order(
                    pair['perp_market_name'], 'sell', order_price, order_size, type_=order_type, client_id=client_id_perp)),
                return_exceptions=True
            )
        elif order_direction == cls.OrderDirection.SPOT_SHORT_PERP_LONG:
            spot_order, perp_order = await asyncio.gather(
                loop.run_in_executor(None, lambda: self.rest_api_client.place_order(
                    pair['perp_market_name'], 'buy', order_price, order_size, type_=order_type, client_id=client_id_perp)),
                loop.run_in_executor(None, lambda: self.rest_api_client.place_order(
                    pair['spot_market_name'], 'sell', order_price, order_size, type_=order_type, client_id=client_id_spot)),
                return_exceptions=True
            )
        exception_descriptions = []
        if isinstance(spot_order, Exception):
            exception_descriptions.append('Failed to create spot order')
        if isinstance(perp_order, Exception):
            exception_descriptions.append('Failed to create spot order')
        if exception_descriptions:
            self.log_error('[pair failed]')
            if isinstance(spot_order, Exception):
                self.log_error(f"- [spot] {pair['spot_market_name']}, {spot_order}")
            if isinstance(perp_order, Exception):
                self.log_error(f"- [perp] {pair['perp_market_name']}, {perp_order}")
            raise Exception(','.join(exception_descriptions))
        return spot_order, perp_order

    async def increase_pair(self, pair: dict,
                            fixed_amount: Decimal = None, fixed_quote_amount: Decimal = None) -> Tuple[dict, dict]:
        cls = self.__class__

        if fixed_amount:
            amount = fixed_amount
        elif fixed_quote_amount:
            amount = fixed_quote_amount / Decimal(pair['spot_price'])
        else:
            amount = pair['min_provide_size']

        if pair['funding_rate'] > 0:
            order_direction = cls.OrderDirection.SPOT_LONG_PERP_SHORT
        elif pair['funding_rate'] < 0:
            order_direction = cls.OrderDirection.SPOT_SHORT_PERP_LONG
        else:
            return None, None

        return await self.make_pair(pair, amount, order_direction)

    async def decrease_pair(self, pair: dict, balance: dict, position: dict,
                            fixed_amount: Decimal = None, fixed_quote_amount: Decimal = None) -> Tuple[dict, dict]:
        cls = self.__class__

        if fixed_amount:
            amount = fixed_amount
        elif fixed_quote_amount:
            amount = fixed_quote_amount / Decimal(pair['spot_price'])
            amount = min(amount, abs(balance['total']), abs(position['net_size']))
        else:
            amount = pair['min_provide_size']

        if balance['total'] > 0 and position['net_size'] < 0:
            order_direction = cls.OrderDirection.SPOT_SHORT_PERP_LONG
        elif balance['total'] < 0 and position['net_size'] > 0:
            order_direction = cls.OrderDirection.SPOT_LONG_PERP_SHORT
        else:
            return None, None

        return await self.make_pair(pair, amount, order_direction)

    def balance_pair(self, pair: dict, balance: Optional[dict], position: Optional[dict]) -> Optional[dict]:
        order_price = None # Send null for market orders
        order_type = 'market' # "limit" or "market"
        ts = int(time.time() * 1000)

        if balance and position:
            if balance['total'] < 0 and position['net_size'] < 0:
                return None
            if balance['total'] > 0 and position['net_size'] > 0:
                return None
            amount = Decimal(str(abs(abs(balance['total']) - abs(position['net_size']))))
            if abs(balance['total']) > abs(position['net_size']):
                if amount < pair['spot_min_provide_size']:
                    return None
                order_size = float(amount.quantize(pair['spot_size_increment'], rounding=ROUND_FLOOR))
                order_market = pair['spot_market_name']
                order_client_id = f'lation_coin_spot_order_{ts}'
                if balance['total'] > 0:
                    order_side = 'sell'
                elif balance['total'] < 0:
                    order_side = 'buy'
            elif abs(balance['total']) < abs(position['net_size']):
                if amount < pair['perp_min_provide_size']:
                    return None
                order_size = float(amount.quantize(pair['perp_size_increment'], rounding=ROUND_FLOOR))
                order_market = pair['perp_market_name']
                order_client_id = f'lation_coin_perp_order_{ts}'
                if position['net_size'] > 0:
                    order_side = 'sell'
                elif position['net_size'] < 0:
                    order_side = 'buy'
        elif balance and not position:
            amount = Decimal(str(abs(balance['total'])))
            if amount < pair['spot_min_provide_size']:
                return None
            order_size = float(amount.quantize(pair['spot_size_increment'], rounding=ROUND_FLOOR))
            order_market = pair['spot_market_name']
            order_client_id = f'lation_coin_spot_order_{ts}'
            if balance['total'] > 0:
                order_side = 'sell'
            elif balance['total'] < 0:
                order_side = 'buy'
        elif not balance and position:
            amount = Decimal(str(abs(position['net_size'])))
            if amount < pair['perp_min_provide_size']:
                return None
            order_size = float(amount.quantize(pair['perp_size_increment'], rounding=ROUND_FLOOR))
            order_market = pair['perp_market_name']
            order_client_id = f'lation_coin_perp_order_{ts}'
            if position['net_size'] > 0:
                order_side = 'sell'
            elif position['net_size'] < 0:
                order_side = 'buy'

        order = self.rest_api_client.place_order(
            order_market, order_side, order_price, order_size, type_=order_type, client_id=order_client_id)
        return order

    async def execute(self):
        current_leverage = -1
        if self.config.increase_pair.enabled or self.config.decrease_pair.enabled:
            current_leverage = self.get_current_leverage()

        # increase pairs
        if self.config.always_increase_pair.enabled or self.config.increase_pair.enabled:
            pair = self.get_best_pair_from_market()
            # only applicable to single side
            if self.config.always_increase_pair.enabled and pair['spread_rate'] > self.config.always_increase_pair.gt_spread_rate:
                spot_order, perp_order = await self.increase_pair(pair, fixed_quote_amount=self.config.always_increase_pair.quote_amount)
                self.log_info(f'[pair always increased]')
                self.log_info(f"- [spot] {spot_order['market']}: {spot_order['side']} amount {spot_order['size']}")
                self.log_info(f"- [perp] {perp_order['market']}: {perp_order['side']} amount {perp_order['size']}")
            elif (
                self.config.increase_pair.enabled and
                current_leverage < self.config.increase_pair.lt_leverage and
                abs(pair['spread_rate']) > self.config.increase_pair.gt_spread_rate
            ):
                leverage_diff = self.config.increase_pair.lt_leverage - current_leverage
                fixed_quote_amount = FTXSpotFuturesArbitrageStrategy.get_quote_amount_from_rules(
                    abs(leverage_diff), self.config.increase_pair.leverage_diff_to_quote_amount_rules)
                spot_order, perp_order = await self.increase_pair(pair, fixed_quote_amount=fixed_quote_amount)
                self.log_info(f'[pair increased] at leverage {current_leverage}')
                self.log_info(f"- [spot] {spot_order['market']}: {spot_order['side']} amount {spot_order['size']}")
                self.log_info(f"- [perp] {perp_order['market']}: {perp_order['side']} amount {perp_order['size']}")

        # decrease pairs
        if self.config.always_decrease_pair.enabled or self.config.decrease_pair.enabled:
            pair, balance, position = self.get_worst_pair_from_asset()
            # only applicable to single side
            if self.config.always_decrease_pair.enabled and pair['spread_rate'] < self.config.always_decrease_pair.lt_spread_rate:
                spot_order, perp_order = await self.decrease_pair(pair, balance, position, fixed_quote_amount=self.config.always_decrease_pair.quote_amount)
                self.log_info(f'[pair always decreased]')
                self.log_info(f"- [spot] {spot_order['market']}: {spot_order['side']} amount {spot_order['size']}")
                self.log_info(f"- [perp] {perp_order['market']}: {perp_order['side']} amount {perp_order['size']}")
            elif (
                self.config.decrease_pair.enabled and
                self.config.decrease_pair.gt_leverage < current_leverage <= self.config.close_pair.gt_leverage and
                pair and abs(pair['spread_rate']) < self.config.decrease_pair.lt_spread_rate
            ):
                leverage_diff = current_leverage - self.config.decrease_pair.gt_leverage
                fixed_quote_amount = FTXSpotFuturesArbitrageStrategy.get_quote_amount_from_rules(
                    abs(leverage_diff), self.config.decrease_pair.leverage_diff_to_quote_amount_rules)
                spot_order, perp_order = await self.decrease_pair(pair, balance, position, fixed_quote_amount=fixed_quote_amount)
                self.log_info(f'[pair decreased] at leverage {current_leverage}')
                self.log_info(f"- [spot] {spot_order['market']}: {spot_order['side']} amount {spot_order['size']}")
                self.log_info(f"- [perp] {perp_order['market']}: {perp_order['side']} amount {perp_order['size']}")

        # close pairs
        if self.config.close_pair.gt_leverage < current_leverage:
            pair, balance, position = self.get_worst_pair_from_asset()
            if pair:
                fixed_amount = Decimal(str(min(abs(balance['total']), abs(position['net_size']))))
                spot_order, perp_order = await self.decrease_pair(pair, balance, position, fixed_amount=fixed_amount)
                self.log_info(f'[pair closed] at leverage {current_leverage}')
                self.log_info(f"- [spot] {spot_order['market']}: {spot_order['side']} amount {spot_order['size']}")
                self.log_info(f"- [perp] {perp_order['market']}: {perp_order['side']} amount {perp_order['size']}")

        # balance pairs
        balance_map, position_map = self.get_asset_map()
        imbalanced_pairs = self.get_imbalanced_pairs(balance_map, position_map)
        for pair in imbalanced_pairs:
            balance = balance_map.get(pair['base_currency'])
            position = position_map.get(pair['perp_market_name'])
            order = self.balance_pair(pair, balance, position)
            if order:
                self.log_info(f'[pair balanced]')
                self.log_info(f"- {order['market']}: {order['side']} amount {order['size']}")

    async def decrease_negative_funding_payment_pairs(self):
        cls = self.__class__
        if not self.config.garbage_collect.enabled:
            return

        local_now = datetime.now()
        funding_payments = self.rest_api_client.list_funding_payments(
            start_time=local_now - timedelta(hours=2), end_time=local_now)
        funding_payment_map = defaultdict(list)
        for fp in funding_payments:
            funding_payment_map[fp['future']].append(fp['payment'])

        evictable_candidates = []
        balance_map, position_map = self.get_asset_map()
        for perp_market_name, payments in funding_payment_map.items():
            if all([p > 0 for p in payments]):
                pair = next(pair for pair in cls.pair_map.values() if pair['perp_market_name'] == perp_market_name)
                balance = balance_map.get(pair['base_currency'])
                position = position_map.get(pair['perp_market_name'])
                if not balance or not position:
                    continue
                if abs(balance['total']) < pair['min_provide_size'] or abs(position['net_size']) < pair['min_provide_size']:
                    continue
                evictable_candidates.append((pair, balance, position))
        if not evictable_candidates:
            return

        market_name_map = self.get_market_name_map()
        if self.should_update_spread_rate():
            self.update_spread_rate(market_name_map)
        for pair, balance, position in evictable_candidates:
            if abs(pair['spread_rate']) < self.config.garbage_collect.lt_spread_rate:
                spot_order, perp_order = await self.decrease_pair(pair, balance, position)

    def should_raise_leverage_alarm(self) -> Tuple[bool, float]:
        current_leverage = self.get_current_leverage()
        return self.config.alarm.enabled and self.config.alarm.gt_leverage < current_leverage, current_leverage


# https://github.com/ftexchange/ftx/blob/master/rest/client.py
class FTXRestAPIClient:

    HOST = 'https://ftx.com/api'

    request_rate_limiter = RateLimiter(30, 1)

    @staticmethod
    def get_page_params(start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, **kwargs) -> dict:
        start_time_ts = None
        if start_time:
            start_time_ts = start_time.timestamp()
        end_time_ts = None
        if end_time:
            end_time_ts = end_time.timestamp()
        return {
            'start_time': start_time_ts,
            'end_time': end_time_ts,
        }

    def __init__(self, api_key: str = None, api_secret: str = None, subaccount_name: str = None):
        self._session = Session()
        self.api_key = api_key
        self.api_secret = api_secret
        self.subaccount_name = subaccount_name

    def _sign_request(self, request: Request):
        ts = int(time.time() * 1000)
        prepared = request.prepare()
        signature_payload = f'{ts}{prepared.method}{prepared.path_url}'.encode()
        if prepared.body:
            signature_payload += prepared.body
        signature = hmac.new(self.api_secret.encode(), signature_payload, 'sha256').hexdigest()
        request.headers['FTX-KEY'] = self.api_key
        request.headers['FTX-SIGN'] = signature
        request.headers['FTX-TS'] = str(ts)
        if self.subaccount_name:
            request.headers['FTX-SUBACCOUNT'] = urllib.parse.quote(self.subaccount_name)

    def _process_response(self, response: Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise
        else:
            if not data['success']:
                raise Exception(data['error'])
            return data['result']

    @request_rate_limiter.wait_strategy
    def request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, FTXRestAPIClient.HOST + path, **kwargs)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    @request_rate_limiter.wait_strategy
    def auth_request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, FTXRestAPIClient.HOST + path, **kwargs)
        self._sign_request(request)
        response = self._session.send(request.prepare())
        return self._process_response(response)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.request('GET', path, params=params)

    def auth_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.auth_request('GET', path, params=params)

    def auth_post(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.auth_request('POST', path, json=params)

    def auth_delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self.auth_request('DELETE', path, json=params)

    # Public Requests

    def list_markets(self) -> List[dict]:
        return self.get('/markets')

    def get_market(self, market_name: str) -> dict:
        return self.get(f'/markets/{market_name}')

    def list_futures(self) -> List[dict]:
        return self.get('/futures')

    def list_funding_rates(self, **kwargs) -> List[dict]:
        return self.get('/funding_rates', FTXRestAPIClient.get_page_params(**kwargs))

    # Auth Requests

    def get_account_info(self) -> dict:
        return self.auth_get('/account')

    def list_wallet_balances(self) -> List[dict]:
        return self.auth_get('/wallet/balances')

    def list_wallet_coins(self) -> List[dict]:
        return self.auth_get('/wallet/coins')

    def list_positions(self) -> List[dict]:
        return self.auth_get('/positions')

    def place_order(self, market: str, side: str, price: float, size: float,
                    type_: str = 'limit', reduce_only: bool = False, ioc: bool = False, post_only: bool = False, client_id: str = None) -> dict:
        return self.auth_post('/orders', {
            'market': market,
            'side': side,
            'price': price,
            'size': size,
            'type': type_,
            'reduceOnly': reduce_only,
            'ioc': ioc,
            'postOnly': post_only,
            'clientId': client_id,
        })

    def delete_order(self, client_order_id: str) -> dict:
        return self.auth_delete(f'/orders/by_client_id/{client_order_id}')

    def list_funding_payments(self, **kwargs) -> List[dict]:
        return self.auth_get('/funding_payments', FTXRestAPIClient.get_page_params(**kwargs))

    def list_spot_margin_borrow_histories(self, **kwargs) -> List[dict]:
        return self.auth_get('/spot_margin/borrow_history', FTXRestAPIClient.get_page_params(**kwargs))
