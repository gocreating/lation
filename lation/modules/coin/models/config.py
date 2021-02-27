from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import JSON, STRING_M_SIZE, Integer, String
from lation.core.orm import Base


class EndUserBitfinexConfig(Base):
    __tablename__ = 'end_user_bitfinex_config'

    end_user_id = Column(Integer, ForeignKey('end_user.id'), index=True)
    end_user = relationship('EndUser', foreign_keys=[end_user_id], backref=backref('end_user_bitfinex_config', uselist=False, cascade='all, delete-orphan'))

    api_key = Column(String(STRING_M_SIZE))
    api_secret = Column(String(STRING_M_SIZE))

    config = Column(JSON)
