import enum

from sqlalchemy import JSON, Column, ForeignKey, Integer, String

from lation.core.orm import Base
from lation.modules.combo.models.mixin import ComboMixin

class LineUser(Base, ComboMixin):
    __tablename__ = 'line_users'

    identifier = Column(String(255))
    accessToken = Column(String(255))
    refreshToken = Column(String(255))
    profile = Column(JSON)
