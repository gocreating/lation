import enum
import hashlib
import hmac
import json
import time
from datetime import datetime, timezone
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

class FundingCreditSchema(BaseModel):
    id: int
    symbol: str
    side: int
    mts_create: datetime
    mts_update: datetime
    amount: float
    flags: Any
    status: str
    rate_type: str
    rate: float
    period: int
    mts_opening: datetime
    mts_last_payout: datetime
    notify: Optional[int]
    hidden: int
    renew: int
    no_close: int
    position_pair: str

class FundingCredit(FundingCreditSchema):
    def __init__(self, raw_data: List[Any]):
        id, symbol, side, mts_create, mts_update, amount, flags, status, rate_type, _, _, rate, period, mts_opening, mts_last_payout, notify, hidden, _, renew, _, no_close, position_pair = raw_data
        super().__init__(id=id, symbol=symbol, side=side, mts_create=mts_create, mts_update=mts_update, amount=amount, flags=flags, status=status, rate_type=rate_type, rate=rate, period=period, mts_opening=mts_opening, mts_last_payout=mts_last_payout, notify=notify, hidden=hidden, renew=renew, no_close=no_close, position_pair=position_pair)

class FundingOfferSchema(BaseModel):
    id: int
    symbol: str
    mts_created: datetime
    mts_updated: datetime
    amount: float
    amount_orig: float
    type: str
    flags: Any
    status: str
    rate: float
    period: int
    notify: int
    hidden: int
    renew: int

class FundingOffer(FundingOfferSchema):
    def __init__(self, raw_data: List[Any]):
        id, symbol, mts_created, mts_updated, amount, amount_orig, type, _, _, flags, status, _, _, _, rate, period, notify, hidden, _, renew, _ = raw_data
        super().__init__(id=id,symbol=symbol,mts_created=mts_created,mts_updated=mts_updated,amount=amount,amount_orig=amount_orig,type=type,flags=flags,status=status,rate=rate,period=period,notify=notify,hidden=hidden,renew=renew)

class UpdateFundingOfferSchema(BaseModel):
    mts: datetime
    type: str
    message_id: Optional[int]
    fundingOffer: FundingOfferSchema
    code: Optional[int]
    status: str
    text: Optional[str]

class UpdateFundingOffer(UpdateFundingOfferSchema):
    def __init__(self, raw_data: List[Any]):
        mts, type, message_id, _, raw_funding_offer, code, status, text = raw_data
        fundingOffer = FundingOffer(raw_funding_offer)
        super().__init__(mts=mts, type=type, message_id=message_id, fundingOffer=fundingOffer, code=code, status=status, text=text)

class LedgerSchema(BaseModel):
    id: int
    currency: str
    mts: datetime
    amount: float
    balance: float
    description: str

class Ledger(LedgerSchema):
    def __init__(self, raw_data: List[Any]):
        id, currency, _, mts, _, amount, balance, _, description = raw_data
        super().__init__(id=id, currency=currency, mts=mts, amount=amount, balance=balance, description=description)

class BitfinexAPIClient(HttpClient):
    DEFAULT_HOST = 'https://api-pub.bitfinex.com/v2'
    AUTH_HOST = 'https://api.bitfinex.com/v2'

    class CurrencyEnum(str, enum.Enum):
        USD = 'USD'

    class LedgerCategoryEnum(int, enum.Enum):
        MARGIN_SWAP_INTEREST_PAYMENT = 28

    class FundingOfferTypeEnum(str, enum.Enum):
        LIMIT = 'LIMIT'
        FRRDELTAVAR = 'FRRDELTAVAR'
        FRRDELTAFIX = 'FRRDELTAFIX'

    def __init__(self, api_key:str=None, api_secret:str=None):
        super().__init__(host=BitfinexAPIClient.DEFAULT_HOST)
        self.api_key = api_key
        self.api_secret = api_secret

    # https://github.com/bitfinexcom/bitfinex-api-py/blob/master/bfxapi/utils/auth.py
    def auth_post(self, path:str, *args, payload:dict={}, **kwargs) -> Response:
        nonce = str(int(round(time.time() * 1000000)))
        signature = f'/api/v2{path}{nonce}{json.dumps(payload)}'
        h = hmac.new(self.api_secret.encode('utf8'), signature.encode('utf8'), hashlib.sha384)
        signature = h.hexdigest()
        res = self.post(f'{BitfinexAPIClient.AUTH_HOST}{path}', *args, headers={
            'bfx-nonce': nonce,
            'bfx-apikey': self.api_key,
            'bfx-signature': signature,
        }, json=payload, **kwargs)
        if res.status_code < 200 or res.status_code > 299:
            raise Exception(f'[Bitfinex API Client] Failed to request path {path}')
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

    def get_user_wallets(self) -> List[WalletSchema]:
        raw_wallets = self.auth_post('/auth/r/wallets')
        return [Wallet(raw_wallet) for raw_wallet in raw_wallets]

    def get_user_ledgers(self, currency:CurrencyEnum, start:datetime=None, end:datetime=None, limit:int=None, category:Optional[LedgerCategoryEnum]=None) -> List[LedgerSchema]:
        params = {}
        payload = {}
        if start != None:
            params['start'] = int(start.replace(tzinfo=timezone.utc).timestamp()) * 1000
        if end != None:
            params['end'] = int(end.replace(tzinfo=timezone.utc).timestamp()) * 1000
        if limit != None:
            params['limit'] = limit
        if category != None:
            payload['category'] = category
        raw_ledgers = self.auth_post(f'/auth/r/ledgers/{currency}/hist', params=params, payload=payload)
        return [Ledger(raw_ledger) for raw_ledger in raw_ledgers]

    def get_user_funding_credits(self, symbol:str) -> List[FundingCreditSchema]:
        raw_funding_credits = self.auth_post(f'/auth/r/funding/credits/{symbol}')
        return [FundingCredit(raw_funding_credit) for raw_funding_credit in raw_funding_credits]

    def get_user_funding_offers(self, symbol:str) -> List[FundingOfferSchema]:
        raw_funding_offers = self.auth_post(f'/auth/r/funding/offers/{symbol}')
        return [FundingOffer(raw_funding_offer) for raw_funding_offer in raw_funding_offers]

    def submit_user_funding_offer(self, type_:FundingOfferTypeEnum, symbol:str, amount:str, daily_rate:str, period:int) -> UpdateFundingOfferSchema:
        raw_submit_funding_offer = self.auth_post(f'/auth/w/funding/offer/submit', payload={
            'type': type_,
            'symbol': symbol,
            'amount': amount,
            'rate': daily_rate,
            'period': period,
            'flags': 0,
        })
        return UpdateFundingOffer(raw_submit_funding_offer)

    def cancel_user_funding_offer(self, offer_id:int) -> UpdateFundingOfferSchema:
        raw_cancel_funding_offer = self.auth_post(f'/auth/w/funding/offer/cancel', payload={ 'id': offer_id })
        return UpdateFundingOffer(raw_cancel_funding_offer)
