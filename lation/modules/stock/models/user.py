import enum

from sqlalchemy import Column, ForeignKey, Integer, String

from lation.core.orm import Base

class User(Base):
    __tablename__ = 'user'

    provider = Column(String(255))
