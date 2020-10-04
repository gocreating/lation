import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer

from lation.core.orm import Base
from lation.modules.combo.models.mixin import ComboMixin

class UserOrder(Base, ComboMixin):
    __tablename__ = 'user_orders'

    userId = Column(Integer, ForeignKey('users.id'))
    userPaymentId = Column(Integer, ForeignKey('user_payments.id'))
    productId = Column(Integer, ForeignKey('products.id'))
    effectiveAt = Column(DateTime)
    dueAt = Column(DateTime)
