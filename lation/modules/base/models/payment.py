from __future__ import annotations
from datetime import datetime
from urllib.parse import quote_plus
from typing import List, Optional

import shortuuid
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, STRING_XS_SIZE, Integer, Numeric, String
from lation.core.env import get_env
from lation.core.orm import Base, JoinedTableInheritanceMixin, SingleTableInheritanceMixin
from lation.modules.base_fastapi.routers.schemas import StatusEnum
from lation.modules.base.models.currency import Currency
from lation.modules.base.vendors.ecpay_payment_sdk import ECPayPaymentSdk


HOST = get_env('HOST')
FRONTEND_HOST = get_env('FRONTEND_HOST')
PAYMENT_GATEWAY_ECPAY_MERCHANT_ID = get_env('PAYMENT_GATEWAY_ECPAY_MERCHANT_ID')
PAYMENT_GATEWAY_ECPAY_HASH_KEY = get_env('PAYMENT_GATEWAY_ECPAY_HASH_KEY')
PAYMENT_GATEWAY_ECPAY_HASH_IV = get_env('PAYMENT_GATEWAY_ECPAY_HASH_IV')
PAYMENT_REDIRECT_URL=f'{FRONTEND_HOST}/payment/result'


class Payment(Base):
    __tablename__ = 'payment'

    payment_gateway_trade_id = Column(Integer, ForeignKey('payment_gateway_trade.id'), index=True)
    payment_gateway_trade = relationship('PaymentGatewayTrade', foreign_keys=[payment_gateway_trade_id])

    billed_amount = Column(Numeric)
    billed_currency_id = Column(Integer, ForeignKey('currency.id'), index=True)
    billed_currency = relationship('Currency', foreign_keys=[billed_currency_id])

    @hybrid_property
    def total_billed_amount(self) -> float:
        return sum([payment_item.billed_amount for payment_item in self.payment_items])


class PaymentItem(Base):
    __tablename__ = 'payment_item'

    payment_id = Column(Integer, ForeignKey('payment.id'), index=True)
    payment = relationship('Payment', foreign_keys=[payment_id], backref=backref('payment_items'))

    item_name = Column(String(STRING_S_SIZE))

    billed_amount = Column(Numeric)
    billed_currency_id = Column(Integer, ForeignKey('currency.id'), index=True)
    billed_currency = relationship('Currency', foreign_keys=[billed_currency_id])


class PaymentGateway(Base, SingleTableInheritanceMixin):
    __tablename__ = 'payment_gateway'

    currencies = association_proxy('payment_gateway_currencies', 'currency')

    @hybrid_property
    def prioritized_currencies(self) -> List[Currency]:
        sorted_payment_gateway_currencies = sorted(self.payment_gateway_currencies, key=lambda pgc: pgc.sequence)
        return [pgc.currency for pgc in sorted_payment_gateway_currencies]

    def generate_trade_number(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def create_trade(self, currency: Currency, *args, **kwargs) -> PaymentGatewayTrade:
        raise NotImplementedError

    def create_order(self, trade: PaymentGatewayTrade, *args, **kwargs):
        raise NotImplementedError

    def get_payment_page_content(self, *args, **kwargs):
        raise NotImplementedError

    def get_success_redirect_url(self, *args, **kwargs):
        raise NotImplementedError

    def get_failure_redirect_url(self, *args, error:Optional[str]=None, **kwargs):
        raise NotImplementedError

    def sync_payment(self, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def verify_payment_result(cls, session: Session, payment_result: Any, *args, **kwargs) -> Tuple(bool, PaymentGatewayTrade):
        raise NotImplementedError

    @classmethod
    def handle_payment_result(cls, session: Session, payment_result: Any, *args, **kwargs):
        raise NotImplementedError


class PaymentGatewayCurrency(Base):
    __tablename__ = 'payment_gateway_currency'

    payment_gateway_id = Column(Integer, ForeignKey('payment_gateway.id'), index=True)
    payment_gateway = relationship('PaymentGateway', foreign_keys=[payment_gateway_id], backref=backref('payment_gateway_currencies'))

    currency_id = Column(Integer, ForeignKey('currency.id'), index=True)
    currency = relationship('Currency', foreign_keys=[currency_id])

    sequence = Column(Integer)


class ECPayPaymentGateway(PaymentGateway):
    __lation__ = {
        'polymorphic_identity': 'ecpay_payment_gateway'
    }

    merchant_id = Column(String(STRING_XS_SIZE))
    hash_key = Column(String(STRING_XS_SIZE))
    hash_iv = Column(String(STRING_XS_SIZE))
    checkout_action_url = Column(String(STRING_M_SIZE))
    query_action_url = Column(String(STRING_M_SIZE))

    def get_sdk(self):
        if not getattr(self, '_sdk', None):
            self._sdk = ECPayPaymentSdk(MerchantID=self.merchant_id if self.merchant_id else PAYMENT_GATEWAY_ECPAY_MERCHANT_ID,
                                        HashKey=self.hash_key if self.hash_key else PAYMENT_GATEWAY_ECPAY_HASH_KEY,
                                        HashIV=self.hash_iv if self.hash_iv else PAYMENT_GATEWAY_ECPAY_HASH_IV)
        return self._sdk

    def generate_trade_number(self, *args, **kwargs) -> str:
        trade_number = shortuuid.ShortUUID().random(length=20)
        return trade_number

    def create_trade(self, currency: Currency, *args, **kwargs) -> ECPayPaymentGatewayTrade:
        return ECPayPaymentGatewayTrade(payment_gateway=self, currency=currency, number=self.generate_trade_number())

    def create_order(self, trade: ECPayPaymentGatewayTrade, *args, amount:int=None, state:dict=None, description:str=None, item_name:str=None, **kwargs):
        sdk = self.get_sdk()
        assert description
        assert item_name
        order_params = {
            'MerchantTradeNo': trade.number,
            # 'StoreID': '',
            'MerchantTradeDate': datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S'),
            # 'PaymentType': 'aio',
            'TotalAmount': int(amount),
            'TradeDesc': description,
            'ItemName': item_name,
            'ReturnURL': f'{HOST}/payment-gateways/ecpay/callbacks/payment',
            'ChoosePayment': 'Credit',
            # 'ClientBackURL': PAYMENT_REDIRECT_URL,
            # 'ItemURL': 'https://www.ecpay.com.tw/item_url.php',
            # 'Remark': '交易備註',
            # 'ChooseSubPayment': '',
            # 'OrderResultURL': PAYMENT_REDIRECT_URL,
            'OrderResultURL': f'{HOST}/payment-gateways/ecpay/callbacks/order-result',
            'NeedExtraPaidInfo': 'Y',
            # 'DeviceSource': '',
            # 'IgnorePayment': '',
            # 'PlatformID': '',
            # 'InvoiceMark': 'N',
            # 'EncryptType': 1,
        }
        if state:
            if len(state) == 1:
                key = state.keys()[0]
                order_params.update({
                    'CustomField1': key,
                    'CustomField2': str(state[key]),
                })
            elif len(state) == 2:
                key1, key2 = state.keys()
                order_params.update({
                    'CustomField1': key1,
                    'CustomField2': str(state[key1]),
                    'CustomField3': key2,
                    'CustomField4': str(state[key2]),
                })
            else:
                raise NotImplementedError
        order = sdk.create_order(order_params)
        return order

    def get_payment_page_content(self, payment_gateway_order, *args, **kwargs):
        sdk = self.get_sdk()
        html = sdk.gen_html_post_form(self.checkout_action_url, payment_gateway_order)
        return html

    def get_success_redirect_url(self, *args, **kwargs):
        return f'{PAYMENT_REDIRECT_URL}?status={StatusEnum.SUCCESS}'

    def get_failure_redirect_url(self, *args, error:Optional[str]=None, **kwargs):
        if not error:
            error = 'ecpay payment failed'
        return f'{PAYMENT_REDIRECT_URL}?status={StatusEnum.FAILED}&error={quote_plus(error)}'


class PaymentGatewayTrade(Base, JoinedTableInheritanceMixin):
    __tablename__ = 'payment_gateway_trade'
    __lation__ = {
        'polymorphic_identity': 'payment_gateway_trade'
    }

    payment_gateway_id = Column(Integer, ForeignKey('payment_gateway.id'), index=True)
    payment_gateway = relationship('PaymentGateway', foreign_keys=[payment_gateway_id])

    currency_id = Column(Integer, ForeignKey('currency.id'), index=True)
    currency = relationship('Currency', foreign_keys=[currency_id])

    number = Column(String(STRING_S_SIZE))
    reference = Column(String(STRING_S_SIZE), comment='An identifier to reference the resource stored in the internal of current gateway')


class ECPayPaymentGatewayTrade(PaymentGatewayTrade):
    __tablename__ = 'ecpay_payment_gateway_trade'
    __lation__ = {
        'polymorphic_identity': 'ecpay_payment_gateway_trade'
    }

    trade_amt = Column(Integer)
    rtn_msg = Column(String(STRING_M_SIZE))
    rtn_code = Column(Integer)
