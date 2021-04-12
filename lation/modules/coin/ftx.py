import hmac
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from requests import Request, Session, Response

from lation.core.utils import RateLimiter, SingletonMetaclass, fallback_empty_kwarg_to_member


class FTXManager(metaclass=SingletonMetaclass):

    @staticmethod
    def lowest_common_price_increment(a: float, b: float):
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
