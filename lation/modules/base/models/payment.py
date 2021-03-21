from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, STRING_XS_SIZE, Float, Integer, String
from lation.core.env import get_env
from lation.core.orm import Base, SingleTableInheritanceMixin
from lation.modules.base.vendors.ecpay_payment_sdk import ECPayPaymentSdk


HOST = get_env('HOST')
FRONTEND_HOST = get_env('FRONTEND_HOST')
PAYMENT_GATEWAY_ECPAY_MERCHANT_ID = get_env('PAYMENT_GATEWAY_ECPAY_MERCHANT_ID')
PAYMENT_GATEWAY_ECPAY_HASH_KEY = get_env('PAYMENT_GATEWAY_ECPAY_HASH_KEY')
PAYMENT_GATEWAY_ECPAY_HASH_IV = get_env('PAYMENT_GATEWAY_ECPAY_HASH_IV')
PAYMENT_REDIRECT_URL=f'{FRONTEND_HOST}/payment/result'


class Payment(Base):
    __tablename__ = 'payment'

    payment_gateway_id = Column(Integer, ForeignKey('payment_gateway.id'), index=True)
    payment_gateway = relationship('PaymentGateway', foreign_keys=[payment_gateway_id])

    @hybrid_property
    def total_billed_amount(self) -> float:
        return sum([payment_item.billed_amount for payment_item in self.payment_items])


class PaymentItem(Base):
    __tablename__ = 'payment_item'

    payment_id = Column(Integer, ForeignKey('payment.id'), index=True)
    payment = relationship('Payment', foreign_keys=[payment_id], backref=backref('payment_items'))

    item_name = Column(String(STRING_S_SIZE))
    billed_amount = Column(Float)


class PaymentGateway(Base, SingleTableInheritanceMixin):
    __tablename__ = 'payment_gateway'

    def create_order(self, *args, **kwargs):
        raise NotImplementedError

    def get_payment_page_content(self, *args, **kwargs):
        raise NotImplementedError

    def get_success_redirect_url(self, *args, **kwargs):
        raise NotImplementedError

    def get_failure_redirect_url(self, *args, error:Optional[str]=None, **kwargs):
        raise NotImplementedError


class ECPayPaymentGateway(PaymentGateway):
    __lation__ = {
        'polymorphic_identity': 'ecpay_payment_gateway'
    }

    merchant_id = Column(String(STRING_XS_SIZE), default=PAYMENT_GATEWAY_ECPAY_MERCHANT_ID)
    hash_key = Column(String(STRING_XS_SIZE), default=PAYMENT_GATEWAY_ECPAY_HASH_KEY)
    hash_iv = Column(String(STRING_XS_SIZE), default=PAYMENT_GATEWAY_ECPAY_HASH_IV)
    action_url = Column(String(STRING_M_SIZE))

    def get_sdk(self):
        if not getattr(self, '_sdk', None):
            self._sdk = ECPayPaymentSdk(MerchantID=self.merchant_id,
                                        HashKey=self.hash_key,
                                        HashIV=self.hash_iv)
        return self._sdk
