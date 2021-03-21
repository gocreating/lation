from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import STRING_S_SIZE, STRING_XS_SIZE, Integer, String
from lation.core.orm import Base


class Platform(Base):
    __tablename__ = 'platform'

    code = Column(String(STRING_XS_SIZE), nullable=False, comment='Platform code')
    name = Column(String(STRING_S_SIZE), nullable=False, comment='Platform name')

    payment_gateways = association_proxy('platform_payment_gateways', 'payment_gateway')


class PlatformPaymentGateway(Base):
    __tablename__ = 'platform_payment_gateway'

    platform_id = Column(Integer, ForeignKey('platform.id'), index=True)
    platform = relationship('Platform', foreign_keys=[platform_id], backref=backref('platform_payment_gateways'))

    payment_gateway_id = Column(Integer, ForeignKey('payment_gateway.id'), index=True)
    payment_gateway = relationship('PaymentGateway', foreign_keys=[payment_gateway_id])
