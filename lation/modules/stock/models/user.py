import enum

from sqlalchemy import Column

from lation.core.database.types import STRING_S_SIZE, String
from lation.core.orm import Base


class User(Base):
    __tablename__ = 'user'

    provider = Column(String(STRING_S_SIZE))
