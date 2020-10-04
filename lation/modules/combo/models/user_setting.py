import enum

from sqlalchemy import JSON, Column, ForeignKey, Integer, String

from lation.core.orm import Base
from lation.modules.combo.models.mixin import ComboMixin

class UserSetting(Base, ComboMixin):
    __tablename__ = 'user_settings'

    userId = Column(Integer, ForeignKey('users.id'))
    type = Column(String(255))
    setting = Column(JSON)
