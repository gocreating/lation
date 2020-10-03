import enum

from sqlalchemy import JSON, Column, String

from lation.modules.base.models.base import Base
from lation.modules.combo.models.mixin import ComboMixin

class ECPayPayment(Base, ComboMixin):
    __tablename__ = 'ec_pay_payments'

    identifier = Column(String(255))
    rawResult = Column(JSON)
