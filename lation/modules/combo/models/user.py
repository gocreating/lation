import enum

from sqlalchemy import Column, ForeignKey, Integer, String

from lation.modules.base.models.base import Base
from lation.modules.combo.models.mixin import ComboMixin

class User(Base, ComboMixin):
    __tablename__ = 'users'

    provider = Column(String(255))
    lineUserId = Column(Integer, ForeignKey('line_users.id'))
