from typing import Tuple

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Session, backref, relationship

from lation.core.database.types import Integer
from lation.modules.base.models.payment import ECPayPaymentGateway, ECPayPaymentGatewayTrade, PaymentGatewayTrade


PaymentGatewayTrade.order_id = Column(Integer, ForeignKey('order.id'), index=True)
PaymentGatewayTrade.order = relationship('Order', foreign_keys=[PaymentGatewayTrade.order_id], backref=backref('payment_gateway_trades'))

@classmethod
def verify_payment_result(cls, session: Session, payment_result: dict, *args, **kwargs) -> Tuple[bool, ECPayPaymentGatewayTrade]:
    # sample payment_result:
    # {'ATMAccBank': '', 'ATMAccNo': '', 'AlipayID': '', 'AlipayTradeNo': '', 'CustomField1': 'lation_app', 'CustomField2': 'coin', 'CustomField3': 'order_id', 'CustomField4': '2', 'ExecTimes': '', 'Frequency': '', 'HandlingCharge': '6', 'ItemName': 'Coin Funding Bot: One Month', 'MerchantID': '3099091', 'MerchantTradeNo': '67iif3kedsGvKyMJ5wGG', ...}

    if payment_result['CustomField3'] != 'order_id':
        return False, None # Invalid ecpay payment result

    trade = session.query(ECPayPaymentGatewayTrade).filter(ECPayPaymentGatewayTrade.number == payment_result['MerchantTradeNo']).one()
    if not trade:
        return False, None # Invalid ecpay payment gateway trade

    order = trade.order
    if not order:
        return False, trade # Invalid ecpay payment result
    if f'{order.id}' != payment_result['CustomField4']:
        return False, trade # Invalid ecpay payment result

    return True, trade

@classmethod
def handle_payment_result(cls, session: Session, payment_result: dict, *args, **kwargs):
    is_verified, trade = cls.verify_payment_result(session, payment_result)
    if not is_verified:
        raise Exception('Invalid payment result')

    trade.reference = payment_result['TradeNo']
    trade.trade_amt = payment_result['TradeAmt']
    # https://github.com/tiangolo/fastapi/issues/309
    # https://github.com/tiangolo/fastapi/issues/2433
    trade.rtn_msg = payment_result['RtnMsg'].encode('Latin-1').decode('utf-8')
    trade.rtn_code = payment_result['RtnCode']
    session.flush()
    if payment_result['RtnCode'] != 1:
        trade.order.charge_fail()
    trade.order.charge_success(trade)


ECPayPaymentGateway.verify_payment_result = verify_payment_result
ECPayPaymentGateway.handle_payment_result = handle_payment_result
