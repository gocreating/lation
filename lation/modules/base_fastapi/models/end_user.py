from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Session, backref, relationship

from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, Boolean, Integer, String
from lation.core.orm import Base


class EndUser(Base):
    __tablename__ = 'end_user'

    encrypted_password = Column(String(STRING_M_SIZE), comment='Encrypted password')

    def login(self):
        pass


class EndUserEmail(Base):
    __tablename__ = 'end_user_email'

    email_address = Column(String(STRING_S_SIZE), index=True, nullable=False, comment='Email address')
    is_verified = Column(Boolean, default=False, index=True, comment='Whether current email has been verified or not')
    is_primary = Column(Boolean, default=False, index=True, comment='Whether current email is primary or not')
    end_user_id = Column(Integer, ForeignKey('end_user.id'), index=True)
    end_user = relationship('EndUser', foreign_keys=[end_user_id], backref=backref('end_user_emails', cascade='all, delete-orphan'))


class EndUserToken(Base):
    __tablename__ = 'end_user_token'
