import enum

from sqlalchemy import JSON, Column, Integer, String

from lation.core.orm import Base
from lation.modules.combo.models.mixin import ComboMixin

class Product(Base, ComboMixin):
    __tablename__ = 'products'

    name = Column(String(255))
    price = Column(Integer)
    currency = Column(String(255))
    props = Column(JSON)
