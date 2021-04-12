from __future__ import annotations
import asyncio
import hmac
import time
import urllib.parse
from decimal import ROUND_FLOOR, Decimal
from typing import Any, Dict, List, Optional, Tuple

from requests import Request, Session, Response

from lation.core.utils import RateLimiter, SingletonMetaclass, fallback_empty_kwarg_to_member


class FTXManager(metaclass=SingletonMetaclass):

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

    def update_market_state(self, quoteCurrency: str = 'USD'):
        markets = self.rest_api_client.list_markets()
        futures = self.rest_api_client.list_futures()

        # TODO: filter markets which has initialized at least 100 days
        self.market_name_map = {market['name']: market
                                for market in markets
                                if market['enabled']}
        self.spot_base_currency_map = {market['baseCurrency']: market
                                       for market in self.market_name_map.values()
                                       if market['type'] == 'spot' and market['quoteCurrency'] == quoteCurrency}
        self.perp_underlying_map = {future['underlying']: future
                                    for future in futures
                                    if future['enabled'] and future['perpetual']}

    def update_funding_rate_state(self):
        funding_rates = self.rest_api_client.list_funding_rates()
        self.funding_rate_name_map = {funding_rate['future']: funding_rate for funding_rate in funding_rates}

    @fallback_empty_kwarg_to_member('rest_api_client')
    def get_leverage(self, rest_api_client: Optional[FTXRestAPIClient] = None):
        account_info = rest_api_client.get_account_info()
        current_leverage = account_info['totalPositionSize'] / account_info['collateral']
        max_leverage = account_info['leverage']
        return {
            'current': current_leverage,
            'max': max_leverage,
        }

    @fallback_empty_kwarg_to_member('rest_api_client')
    async def place_spot_perp_order(self, base_currency: str,
                                    base_amount: Optional[Decimal] = None,
                                    quote_amount: Optional[Decimal] = None, quote_currency: str = 'USD',
                                    rest_api_client: Optional[FTXRestAPIClient] = None) -> Tuple[dict, dict]:
        if (base_amount and quote_amount) or (not base_amount and not quote_amount):
            raise Exception('Either `base_amount` or `quote_amount` is requried')
        spot_market_name = f'{base_currency}/{quote_currency}'
        perp_market_name = f'{base_currency}-PERP'
        spot_market = self.market_name_map.get(spot_market_name, None)
        perp_market = self.market_name_map.get(perp_market_name, None)
        if not spot_market or not perp_market:
            raise Exception('Market not found')

        min_order_size = max(spot_market['minProvideSize'], perp_market['minProvideSize'])
        size_increment = Decimal(str(FTXManager.lowest_common_size_increment(
            spot_market['sizeIncrement'], perp_market['sizeIncrement'])))
        if not base_amount:
            recent_spot_market = rest_api_client.get_market(spot_market_name)
            spot_ask = Decimal(str(recent_spot_market['ask']))
            base_amount = quote_amount / spot_ask
        order_size = float(base_amount.quantize(size_increment.normalize(), rounding=ROUND_FLOOR))
        if order_size < min_order_size:
            raise Exception(f'`quote_amount` is too small. Please provide at least `{quote_currency} {min_order_size * float(spot_ask)}`')
        order_price = None # Send null for market orders
        order_type = 'market' # "limit" or "market"
        ts = int(time.time() * 1000)
        client_id_spot = f'lation_order_{ts}_spot'
        client_id_perp = f'lation_order_{ts}_perp'

        # TODO: should allocate at least 2 requests capacity
        loop = asyncio.get_running_loop()
        spot_order, perp_order = await asyncio.gather(
            loop.run_in_executor(None, lambda: rest_api_client.place_order(spot_market_name, 'buy', order_price, order_size,
                                                                           type_=order_type, client_id=client_id_spot)),
            loop.run_in_executor(None, lambda: rest_api_client.place_order(perp_market_name, 'sell', order_price, order_size,
                                                                           type_=order_type, client_id=client_id_perp)),
            return_exceptions=True
        )
        if isinstance(spot_order, Exception) ^ isinstance(perp_order, Exception):
            # TODO: place another market order to compensate the balance
            raise Exception('Failed to create either spot or perp order')
        elif isinstance(spot_order, Exception) and isinstance(perp_order, Exception):
            raise Exception('Failed to create both spot and perp orders')
        return spot_order, perp_order


# https://github.com/ftexchange/ftx/blob/master/rest/client.py
class FTXRestAPIClient:

    HOST = 'https://ftx.com/api'

    request_rate_limiter = RateLimiter(30, 1)

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

    def list_funding_payments(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[dict]:
        start_time_ts = None
        if start_time:
            start_time_ts = start_time.timestamp()
        end_time_ts = None
        if end_time:
            end_time_ts = end_time.timestamp()
        return self.auth_get('/funding_payments', {
            'start_time': start_time_ts,
            'end_time': end_time_ts,
        })

ftx_manager = FTXManager()
