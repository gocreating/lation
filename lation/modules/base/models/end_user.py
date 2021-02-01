from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Session, backref, relationship

from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, Boolean, DateTime, Integer, String
from lation.core.orm import Base, SingleTableInheritanceMixin


class EndUser(Base):
    __tablename__ = 'end_user'

    encrypted_password = Column(String(STRING_M_SIZE))
    last_login_time = Column(DateTime)
    is_active = Column(Boolean, default=True, index=True)


class EndUserEmail(Base):
    __tablename__ = 'end_user_email'

    email_address = Column(String(STRING_S_SIZE), index=True, nullable=False, comment='Email address')
    is_verified = Column(Boolean, default=False, index=True, comment='Whether current email has been verified or not')
    is_primary = Column(Boolean, default=False, index=True, comment='Whether current email is primary or not')
    end_user_id = Column(Integer, ForeignKey('end_user.id'), index=True)
    end_user = relationship('EndUser', foreign_keys=[end_user_id], backref=backref('end_user_emails', cascade='all, delete-orphan'))


class EndUserToken(Base, SingleTableInheritanceMixin):
    __tablename__ = 'end_user_token'

    end_user_id = Column(Integer, ForeignKey('end_user.id'), index=True)
    end_user = relationship('EndUser', foreign_keys=[end_user_id])

    value = Column(String(STRING_M_SIZE), index=True, comment='Token value')
    expiration_time = Column(DateTime, index=True, comment='Expiration time (UTC+0)')
    is_active = Column(Boolean, default=True, index=True)
