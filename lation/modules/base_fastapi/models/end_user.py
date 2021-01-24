from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.orm import Session

from lation.core.database.types import JSON, STRING_L_SIZE, STRING_M_SIZE, STRING_S_SIZE, STRING_XS_SIZE, Integer, String
from lation.core.orm import Base, JoinedTableInheritanceMixin
from lation.modules.base.schemas.oauth import \
    GoogleTokenSchema, GoogleIdTokenPayloadSchema, GoogleUserinfoSchema, \
    LineTokenSchema, LineIdTokenPayloadSchema, LineUserinfoSchema


class EndUser(Base, JoinedTableInheritanceMixin):
    __tablename__ = 'end_user'
    __lation__ = {
        'polymorphic_identity': 'end_user'
    }


class LocalEndUser(EndUser):
    __tablename__ = 'local_end_user'
    __lation__ = {
        'polymorphic_identity': 'local_end_user'
    }

    encrypted_password = Column(String(STRING_M_SIZE), comment='Encrypted password')


class OAuthMixin:
    account_identifier = Column(String(STRING_S_SIZE), unique=True)
    profile = Column(JSON)

    access_token = Column(String(STRING_M_SIZE))
    token_type = Column(String(STRING_XS_SIZE))
    refresh_token = Column(String(STRING_M_SIZE))
    expires_in = Column(Integer)
    scope = Column(String(STRING_L_SIZE))
    id_token = Column(String(STRING_L_SIZE))

    @classmethod
    def instantiate_from_scheme_data(cls, session:Session, token_data:BaseModel, id_token_payload_data:BaseModel, userinfo_data:BaseModel):
        raise NotImplementedError


class GoogleEndUser(EndUser, OAuthMixin):
    __tablename__ = 'google_end_user'
    __lation__ = {
        'polymorphic_identity': 'google_end_user'
    }

    @classmethod
    def instantiate_from_scheme_data(cls, session:Session, token_data:GoogleTokenSchema, id_token_payload_data:GoogleIdTokenPayloadSchema, userinfo_data:GoogleUserinfoSchema) -> GoogleEndUser:
        google_end_user = session.query(cls)\
            .filter(cls.account_identifier == userinfo_data.sub)\
            .one_or_none()
        if not google_end_user:
            google_end_user = cls()
        google_end_user.account_identifier = userinfo_data.sub
        google_end_user.profile = userinfo_data.dict()
        google_end_user.access_token = token_data.access_token
        google_end_user.token_type = token_data.token_type
        google_end_user.refresh_token = token_data.refresh_token
        google_end_user.expires_in = token_data.expires_in
        google_end_user.scope = token_data.scope
        google_end_user.id_token = token_data.id_token
        return google_end_user


class LineEndUser(EndUser, OAuthMixin):
    __tablename__ = 'line_end_user'
    __lation__ = {
        'polymorphic_identity': 'line_end_user'
    }

    @classmethod
    def instantiate_from_scheme_data(cls, session:Session, token_data:LineTokenSchema, id_token_payload_data:LineIdTokenPayloadSchema, userinfo_data:LineUserinfoSchema) -> LineEndUser:
        line_end_user = session.query(cls)\
            .filter(cls.account_identifier == userinfo_data.userId)\
            .one_or_none()
        if not line_end_user:
            line_end_user = cls()
        if not id_token_payload_data.email:
            raise ValueError('Email is required')
        line_end_user.account_identifier = userinfo_data.userId
        line_end_user.profile = userinfo_data.dict()
        line_end_user.access_token = token_data.access_token
        line_end_user.token_type = token_data.token_type
        line_end_user.refresh_token = token_data.refresh_token
        line_end_user.expires_in = token_data.expires_in
        line_end_user.scope = token_data.scope
        line_end_user.id_token = token_data.id_token
        return line_end_user
