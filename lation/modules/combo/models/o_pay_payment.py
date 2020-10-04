import enum

from sqlalchemy import JSON, Column, String

from lation.core.orm import Base
from lation.modules.combo.models.mixin import ComboMixin

class OPayPayment(Base, ComboMixin):
    __tablename__ = 'o_pay_payments'

    identifier = Column(String(255))
    rawResult = Column(JSON)
