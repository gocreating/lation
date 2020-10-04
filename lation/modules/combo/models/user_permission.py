import enum

from sqlalchemy import Column, ForeignKey, Integer, String

from lation.core.orm import Base
from lation.modules.combo.models.mixin import ComboMixin

class UserPermission(Base, ComboMixin):
    __tablename__ = 'user_permissions'

    userId = Column(Integer, ForeignKey('users.id'))
    permissionName = Column(String(255))
