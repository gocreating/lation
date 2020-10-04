import enum

from sqlalchemy import Column, DateTime, String, Text

from lation.core.orm import Base

class Session(Base):
    __tablename__ = 'Session'

    sid = Column(String(36), primary_key=True)
    expires = Column(DateTime)
    data = Column(Text)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
