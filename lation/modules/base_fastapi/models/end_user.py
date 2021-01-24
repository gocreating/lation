from __future__ import annotations
from sqlalchemy import Column

from lation.core.database.types import JSON, STRING_L_SIZE, STRING_M_SIZE, STRING_S_SIZE, STRING_XS_SIZE, Integer, String
from lation.core.orm import Base, JoinedTableInheritanceMixin
from lation.modules.base.schemas.oauth import \
    GoogleTokenSchema, GoogleUserinfoSchema, \
    LineTokenSchema, LineUserinfoSchema


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

    @classmethod
    def get_or_new_from_scheme_data(cls, token_data:dict, userinfo_data:dict):
        raise NotImplementedError


class GoogleEndUser(EndUser, OAuthMixin):
    __tablename__ = 'google_end_user'
    __lation__ = {
        'polymorphic_identity': 'google_end_user'
    }

    @classmethod
    def get_or_new_from_scheme_data(cls, token_data:GoogleTokenSchema, userinfo_data:GoogleUserinfoSchema) -> GoogleEndUser:
        from lation.modules.base_fastapi.base_fastapi import global_get_session
        session = global_get_session()
        google_end_user = session.query(GoogleEndUser)\
            .filter(GoogleEndUser.account_identifier == userinfo_data.sub)\
            .one_or_none()
        if not google_end_user:
            google_end_user = cls(account_identifier=userinfo_data.sub,
                                  profile=userinfo_data,
                                  access_token=token_data.access_token,
                                  token_type=token_data.token_type,
                                  refresh_token=token_data.refresh_token,
                                  expires_in=token_data.expires_in,
                                  scope=token_data.scope)
        return google_end_user


class LineEndUser(EndUser, OAuthMixin):
    __tablename__ = 'line_end_user'
    __lation__ = {
        'polymorphic_identity': 'line_end_user'
    }

    @classmethod
    def get_or_new_from_scheme_data(cls, token_data:LineTokenSchema, userinfo_data:LineUserinfoSchema) -> LineEndUser:
        from lation.modules.base_fastapi.base_fastapi import global_get_session
        session = global_get_session()
        line_end_user = session.query(LineEndUser)\
            .filter(LineEndUser.account_identifier == userinfo_data.userId)\
            .one_or_none()
        if not line_end_user:
            line_end_user = cls(account_identifier=userinfo_data.userId,
                                profile=userinfo_data,
                                access_token=token_data.access_token,
                                token_type=token_data.token_type,
                                refresh_token=token_data.refresh_token,
                                expires_in=token_data.expires_in,
                                scope=token_data.scope)
        return line_end_user
