from __future__ import annotations
import asyncio
import enum
import hmac
import time
import urllib.parse
from decimal import ROUND_FLOOR, Decimal
from typing import Any, Dict, List, Optional, Tuple

from requests import Request, Session, Response

from lation.core.utils import RateLimiter, SingletonMetaclass, fallback_empty_kwarg_to_member


# https://help.ftx.com/hc/en-us/articles/360031149632-Non-USD-Collateral
NON_USD_COLLATERALS = ['1INCH', 'AAPL', 'AAVE', 'ABNB', 'ACB', 'ALPHA', 'AMC', 'AMD', 'AMZN', 'APHA', 'ARKK', 'AUD', 'BABA', 'BADGER', 'BAND', 'BAO', 'BB', 'BCH', 'BILI', 'BITW', 'BNB', 'BNT', 'BNTX', 'BRL', 'BRZ', 'BTC', 'BTMX', 'BUSD', 'BVOL', 'BYND', 'CAD', 'CBSE', 'CEL', 'CGC', 'CHF', 'CRON', 'CUSDT', 'DAI', 'DOGE', 'ETH', 'ETHE', 'EUR', 'FB', 'FIDA', 'FTM', 'FTT', 'GBP', 'GBTC', 'GDX', 'GDXJ', 'GLD', 'GLXY', 'GME', 'GOOGL', 'GRT', 'HKD', 'HOLY', 'HOOD', 'HT', 'HUSD', 'HXRO', 'IBVOL', 'KIN', 'KNC', 'LEND', 'LEO', 'LINK', 'LRC', 'LTC', 'MATIC', 'MKR', 'MOB', 'MRNA', 'MSTR', 'NFLX', 'NIO', 'NOK', 'NVDA', 'OKB', 'OMG', 'PAX', 'PAXG', 'PENN', 'PFE', 'PYPL', 'RAY', 'REN', 'RSR', 'RUNE', 'SECO', 'SGD', 'SLV', 'SNX', 'SOL', 'SPY', 'SQ', 'SRM', 'SUSHI', 'SXP', 'TLRY', 'TOMO', 'TRX', 'TRY', 'TRYB', 'TSLA', 'TSM', 'TUSD', 'TWTR', 'UBER', 'UNI', 'USD', 'USDC', 'USDT', 'USO', 'WBTC', 'WUSDC', 'XAUT', 'XRP', 'YFI', 'ZAR', 'ZM', 'ZRX']


class FTXManager(metaclass=SingletonMetaclass):

    class QuoteCurrencyEnum(str, enum.Enum):
        USD = 'USD'
        USDT = 'USDT'

    @staticmethod
    def lowest_common_price_increment(a: float, b: float):
        # FIXME: actually this should be float-version lcm(a, b)
        return max(a, b)

    @staticmethod
    def lowest_common_size_increment(a: float, b: float):
        # FIXME: actually this should be float-version lcm(a, b)
        return max(a, b)

    def __init__(self):
        self.rest_api_client = FTXRestAPIClient()
        self.market_name_map = {}
        self.spot_base_currency_map = {}
        self.perp_underlying_map = {}
        self.funding_rate_name_map = {}

        self.alarm_enabled = True
        self.leverage_alarm = 14
        self.strategy_enabled = True
        self.leverage_low = 11
        self.leverage_high = 13

    def update_market_state(self):
        markets = self.rest_api_client.list_markets()
        futures = self.rest_api_client.list_futures()

        self.market_name_map = {market['name']: market
                                for market in markets
                                if market['enabled']}
        self.spot_base_currency_map = {market['baseCurrency']: market
                                       for market in self.market_name_map.values()
                                       if market['type'] == 'spot'}
        self.perp_underlying_map = {future['underlying']: future
                                    for future in futures
                                    if future['enabled'] and future['perpetual']}

    def update_funding_rate_state(self):
        funding_rates = self.rest_api_client.list_funding_rates()
        self.funding_rate_name_map = {funding_rate['future']: funding_rate for funding_rate in funding_rates}

    def list_spot_perp_base_currencies(self) -> List[str]:
        spot_base_currency_map = self.spot_base_currency_map
        perp_underlying_map = self.perp_underlying_map
        base_currencies = set(spot_base_currency_map.keys())\
            .intersection(set(perp_underlying_map.keys()))\
            .intersection(set(NON_USD_COLLATERALS))
        return base_currencies

    def get_spot_perp_market(self, base_currency: str, quote_currency: QuoteCurrencyEnum) -> Tuple[dict, dict]:
        spot_market_name = f'{base_currency}/{quote_currency.value}'
        perp_market_name = f'{base_currency}-PERP'
        spot_market = self.market_name_map.get(spot_market_name, None)
        perp_market = self.market_name_map.get(perp_market_name, None)
        if not spot_market or not perp_market:
            raise Exception('Market not found')
        return spot_market, perp_market

    @fallback_empty_kwarg_to_member('rest_api_client')
    def get_risk_index(self, rest_api_client: Optional[FTXRestAPIClient] = None):
        account_info = rest_api_client.get_account_info()
        # current_leverage = account_info['totalPositionSize'] / account_info['collateral']
        return {
            'raw': {
                'total_account_value': account_info['totalAccountValue'],
                'collateral': account_info['collateral'],
                'total_position_size': account_info['totalPositionSize'],
                'liquidating': account_info['liquidating'],
            },
            'margin_fraction': {
                'current': account_info['marginFraction'],
                'initial_requirement': account_info['initialMarginRequirement'],
                'maintenance_requirement': account_info['maintenanceMarginRequirement'],
                'open': account_info['openMarginFraction'],
            },
            'leverage': {
                'current': 1 / account_info['marginFraction'],
                'initial_requirement': 1 / account_info['initialMarginRequirement'],
                'maintenance_requirement': 1 / account_info['maintenanceMarginRequirement'],
                'open': 1 / account_info['openMarginFraction'],
                'max': account_info['leverage'],
            },
        }

    @fallback_empty_kwarg_to_member('rest_api_client')
    async def place_spot_perp_order(self, base_currency: str,
                                    base_amount: Optional[Decimal] = None,
                                    quote_amount: Optional[Decimal] = None,
                                    quote_currency: Optional[QuoteCurrencyEnum] = QuoteCurrencyEnum.USD,
                                    rest_api_client: Optional[FTXRestAPIClient] = None,
                                    reverse_side: Optional[bool] = False) -> Tuple[dict, dict]:
        if not base_amount and not quote_amount:
            raise Exception('Either `base_amount` or `quote_amount` is requried')
        spot_market, perp_market = self.get_spot_perp_market(base_currency, quote_currency)
        spot_market_name = spot_market['name']
        perp_market_name = perp_market['name']

        min_order_size = max(spot_market['minProvideSize'], perp_market['minProvideSize'])
        size_increment = Decimal(str(FTXManager.lowest_common_size_increment(
            spot_market['sizeIncrement'], perp_market['sizeIncrement'])))
        if base_amount and quote_amount:
            recent_spot_market = rest_api_client.get_market(spot_market_name)
            spot_price = Decimal(str(recent_spot_market['bid' if reverse_side else 'ask']))
            derived_base_amount = quote_amount / spot_price
            base_amount = min(base_amount, derived_base_amount)
        elif not base_amount:
            recent_spot_market = rest_api_client.get_market(spot_market_name)
            spot_price = Decimal(str(recent_spot_market['bid' if reverse_side else 'ask']))
            base_amount = quote_amount / spot_price
        order_size = float(base_amount.quantize(size_increment.normalize(), rounding=ROUND_FLOOR))
        if order_size < min_order_size:
            raise Exception(f'`quote_amount` is too small. Please provide at least `{quote_currency.value} {min_order_size * float(spot_ask)}`')
        order_price = None # Send null for market orders
        order_type = 'market' # "limit" or "market"
        ts = int(time.time() * 1000)
        client_id_spot = f'lation_order_{ts}_spot'
        client_id_perp = f'lation_order_{ts}_perp'

        # TODO: should allocate at least 2 requests capacity
        loop = asyncio.get_running_loop()
        if not reverse_side:
            spot_order, perp_order = await asyncio.gather(
                loop.run_in_executor(None, lambda: rest_api_client.place_order(spot_market_name, 'buy', order_price, order_size,
                                                                               type_=order_type, client_id=client_id_spot)),
                loop.run_in_executor(None, lambda: rest_api_client.place_order(perp_market_name, 'sell', order_price, order_size,
                                                                               type_=order_type, client_id=client_id_perp)),
                return_exceptions=True
            )
        else:
            perp_order, spot_order = await asyncio.gather(
                loop.run_in_executor(None, lambda: rest_api_client.place_order(perp_market_name, 'buy', order_price, order_size,
                                                                               type_=order_type, client_id=client_id_perp)),
                loop.run_in_executor(None, lambda: rest_api_client.place_order(spot_market_name, 'sell', order_price, order_size,
                                                                               type_=order_type, client_id=client_id_spot)),
                return_exceptions=True
            )

        if isinstance(spot_order, Exception) ^ isinstance(perp_order, Exception):
            # TODO: place another market order to compensate the balance
            raise Exception('Failed to create either spot or perp order')
        elif isinstance(spot_order, Exception) and isinstance(perp_order, Exception):
            raise Exception('Failed to create both spot and perp orders')
        return spot_order, perp_order

    @fallback_empty_kwarg_to_member('rest_api_client')
    def place_spot_perp_balancing_order(self, base_currency: str,
                                        quote_currency: Optional[QuoteCurrencyEnum] = QuoteCurrencyEnum.USD,
                                        rest_api_client: Optional[FTXRestAPIClient] = None) -> dict:
        spot_market, perp_market = self.get_spot_perp_market(base_currency, quote_currency)
        spot_market_name = spot_market['name']
        perp_market_name = perp_market['name']

        balances = rest_api_client.list_wallet_balances()
        positions = rest_api_client.list_positions()
        spot_balance = next((balance for balance in balances if balance['coin'] == base_currency), None)
        perp_position = next((position for position in positions if position['future'] == perp_market_name), None)
        if not spot_balance or not perp_position:
            raise Exception('Either spot balance or perp position does not exist')

        total_spot_balance = spot_balance['total']
        perp_position_size = perp_position['size']
        perp_size_increment = Decimal(str(perp_market['sizeIncrement']))
        if total_spot_balance < perp_position_size:
            base_amount = Decimal(str(perp_position_size - total_spot_balance))
            order_type = 'buy'
        elif total_spot_balance > perp_position_size:
            base_amount = Decimal(str(total_spot_balance - perp_position_size))
            order_type = 'sell'
        order_size = float(base_amount.quantize(perp_size_increment.normalize(), rounding=ROUND_FLOOR))
        if order_size < perp_market['minProvideSize']:
            raise Exception('Difference between balance amount and position size is too small')
        perp_order = rest_api_client.place_order(perp_market_name, order_type, None, order_size, type_='market')
        return perp_order

    @fallback_empty_kwarg_to_member('rest_api_client')
    async def apply_spot_futures_arbitrage_strategy_iteration(self, leverage_low, leverage_high,
                                                              rest_api_client: Optional[FTXRestAPIClient] = None):
        risk_index = self.get_risk_index(rest_api_client=rest_api_client)
        current_leverage = risk_index['leverage']['current']
        if leverage_low <= current_leverage <= leverage_high:
            return

        base_currencies = self.list_spot_perp_base_currencies()
        pairs = [{
            'base_currency': self.spot_base_currency_map[currency]['baseCurrency'],
            'quote_currency': self.spot_base_currency_map[currency]['quoteCurrency'],
            'spot_name': self.spot_base_currency_map[currency]['name'],
            'perp_name': self.perp_underlying_map[currency]['name'],
            'funding_rate_1h': self.funding_rate_name_map[self.perp_underlying_map[currency]['name']]['rate'],
        } for currency in base_currencies]
        pairs = sorted(pairs, key=lambda p: p['funding_rate_1h'], reverse=True)

        if current_leverage < leverage_low:
            # buy spot & create position
            can_buy = (risk_index['margin_fraction']['current'] > risk_index['margin_fraction']['initial_requirement'])
            if not can_buy:
                return
            pair = pairs[0]
            if pair['funding_rate_1h'] < 0:
                return
            quote_currency = next(e for e in FTXManager.QuoteCurrencyEnum if e.value == pair['quote_currency'])
            spot_market, perp_market = self.get_spot_perp_market(pair['base_currency'], quote_currency)
            base_amount = max(spot_market['minProvideSize'], perp_market['minProvideSize'])
            spot_order, perp_order = await self.place_spot_perp_order(pair['base_currency'],
                                                                      base_amount=Decimal(str(base_amount)),
                                                                      quote_currency=quote_currency,
                                                                      quote_amount=Decimal('20'),
                                                                      rest_api_client=rest_api_client)

        elif current_leverage > leverage_high:
            # sell spot & close position
            account_info = rest_api_client.get_account_info()
            positions = account_info['positions']
            position_map = {p['future']: p for p in positions}
            position_future_names = [p['future'] for p in positions]
            balances = rest_api_client.list_wallet_balances()
            balance_map = {b['coin']: b for b in balances}
            balance_coin_names = [b['coin'] for b in balances]

            closable_pairs = []
            for pair in pairs:
                if pair['perp_name'] not in position_future_names or pair['base_currency'] not in balance_coin_names:
                    continue
                quote_currency = next(e for e in FTXManager.QuoteCurrencyEnum if e.value == pair['quote_currency'])
                spot_market, perp_market = self.get_spot_perp_market(pair['base_currency'], quote_currency)
                if position_map[pair['perp_name']]['openSize'] < perp_market['minProvideSize']:
                    continue
                if balance_map[pair['base_currency']]['total'] < spot_market['minProvideSize']:
                    continue
                closable_pairs.append(pair)

            if len(closable_pairs) == 0:
                return
            pair = closable_pairs[-1] # pair of lowest funding rate
            quote_currency = next(e for e in FTXManager.QuoteCurrencyEnum if e.value == pair['quote_currency'])
            spot_market, perp_market = self.get_spot_perp_market(pair['base_currency'], quote_currency)
            base_amount = max(spot_market['minProvideSize'], perp_market['minProvideSize'])
            spot_order, perp_order = await self.place_spot_perp_order(pair['base_currency'],
                                                                      base_amount=Decimal(str(base_amount)),
                                                                      quote_currency=quote_currency,
                                                                      rest_api_client=rest_api_client,
                                                                      reverse_side=True)


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

    def list_funding_rates(self) -> List[dict]:
        return self.get('/funding_rates')

    # Auth Requests

    def get_account_info(self) -> dict:
        return self.auth_get('/account')

    def list_wallet_balances(self) -> List[dict]:
        return self.auth_get('/wallet/balances')

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

ftx_manager = FTXManager()
