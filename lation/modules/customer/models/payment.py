from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import Integer
from lation.modules.base.models.payment import PaymentGatewayTrade


PaymentGatewayTrade.order_id = Column(Integer, ForeignKey('order.id'), index=True)
PaymentGatewayTrade.order = relationship('Order', foreign_keys=[PaymentGatewayTrade.order_id], backref=backref('payment_gateway_trades'))

