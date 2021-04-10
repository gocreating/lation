import hmac
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from requests import Request, Session, Response


# https://github.com/ftexchange/ftx/blob/master/rest/client.py
class FTXRestAPIClient:

    HOST = 'https://ftx.com/api'

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

    def request(self, method: str, path: str, **kwargs) -> Any:
        request = Request(method, FTXRestAPIClient.HOST + path, **kwargs)
        response = self._session.send(request.prepare())
        return self._process_response(response)

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

    # Public Requests

    def list_markets(self) -> List[dict]:
        return self.get('/markets')

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
