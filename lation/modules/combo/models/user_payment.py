import enum

from sqlalchemy import Column, ForeignKey, Integer, String

from lation.modules.base.models.base import Base
from lation.modules.combo.models.mixin import ComboMixin

class UserPayment(Base, ComboMixin):
    __tablename__ = 'user_payments'

    userId = Column(Integer, ForeignKey('users.id'))
    provider = Column(String(255))
    providerPaymentId = Column(Integer)
    status = Column(String(255))
    remark = Column(String(255))
