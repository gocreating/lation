import hashlib
import hmac
import json as py_json
import time
from typing import Any, List, Literal, Optional

from pydantic import BaseModel
from lation.modules.base.http_client import HttpClient, Response


class WalletSchema(BaseModel):
    wallet_type: str
    currency: str
    balance: float
    unsettled_interest: float
    available_balance: float
    last_change: Optional[str]
    trade_details: Optional[dict]

class Wallet(WalletSchema):
    def __init__(self, raw_data: List[Any]):
        wallet_type, currency, balance, unsettled_interest, available_balance, last_change, trade_details = raw_data
        super().__init__(wallet_type=wallet_type, currency=currency, balance=balance, unsettled_interest=unsettled_interest, available_balance=available_balance, last_change=last_change, trade_details=trade_details)

class BitfinexAPIClient(HttpClient):
    DEFAULT_HOST = 'https://api-pub.bitfinex.com/v2'
    AUTH_HOST = 'https://api.bitfinex.com/v2'

    def __init__(self, api_key:str=None, api_secret:str=None):
        super().__init__(host=BitfinexAPIClient.DEFAULT_HOST)
        self.api_key = api_key
        self.api_secret = api_secret

    # https://github.com/bitfinexcom/bitfinex-api-py/blob/master/bfxapi/utils/auth.py
    def auth_post_json(self, path:str, *args, json:dict={}, **kwargs) -> Response:
        nonce = str(int(round(time.time() * 1000000)))
        signature = f'/api/v2{path}{nonce}{py_json.dumps(json)}'
        h = hmac.new(self.api_secret.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
        signature = h.hexdigest()
        res = self.post(f'{BitfinexAPIClient.AUTH_HOST}{path}', *args, headers={
            'bfx-nonce': nonce,
            'bfx-apikey': self.api_key,
            'bfx-signature': signature,
        }, json=json, **kwargs)
        return res.json()

    def get_book(self, symbol:str, precision:Literal['P0', 'P1', 'P2', 'P3', 'P4', 'R0'], len_:Literal[1, 25, 100]) -> Response:
        data = self.get_json(f'/book/{symbol}/{precision}', params={ 'len': len_ })
        if not symbol.startswith('f'):
            raise NotImplementedError
        sell_data = data[:len_]
        buy_data = data[len_:]
        book = {
            'sell': {
                'rate': [d[0] for d in sell_data],
                'period': [d[1] for d in sell_data],
                'count': [d[2] for d in sell_data],
                'amount': [d[3] for d in sell_data],
            },
            'buy': {
                'rate': [d[0] for d in buy_data],
                'period': [d[1] for d in buy_data],
                'count': [d[2] for d in buy_data],
                'amount': [d[3] for d in buy_data],
            },
        }
        return book

    def get_user_wallet(self) -> List[WalletSchema]:
        raw_wallets = self.auth_post_json('/auth/r/wallets')
        return [Wallet(raw_wallet) for raw_wallet in raw_wallets]