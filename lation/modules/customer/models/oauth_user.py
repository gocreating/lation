from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Session, backref, relationship

from lation.core.database.types import JSON, STRING_L_SIZE, STRING_M_SIZE, STRING_S_SIZE, STRING_XS_SIZE, Integer, String
from lation.core.orm import Base, JoinedTableInheritanceMixin
from lation.modules.base.models.end_user import EndUser, EndUserEmail
from lation.modules.customer.schemas.oauth import BaseAuthorizationSchema, GoogleAuthorizationSchema, LineAuthorizationSchema


class OIDCMixin:
    id_token = Column(String(STRING_L_SIZE))


class OAuthUser(Base, JoinedTableInheritanceMixin):
    __tablename__ = 'oauth_user'
    __lation__ = {
        'polymorphic_identity': 'oauth_user'
    }

    end_user_id = Column(Integer, ForeignKey('end_user.id'), index=True)
    end_user = relationship('EndUser', foreign_keys=[end_user_id], backref=backref('oauth_users', cascade='all, delete-orphan'))

    account_identifier = Column(String(STRING_S_SIZE), unique=True)
    profile = Column(JSON)

    @classmethod
    def login(cls, session:Session, auth:BaseAuthorizationSchema) -> OAuthUserToken:
        raise NotImplementedError


class OAuthUserToken(Base, JoinedTableInheritanceMixin):
    __tablename__ = 'oauth_user_token'
    __lation__ = {
        'polymorphic_identity': 'oauth_user_token'
    }

    oauth_user_id = Column(Integer, ForeignKey('oauth_user.id'), index=True)
    oauth_user = relationship('OAuthUser', foreign_keys=[oauth_user_id], backref=backref('oauth_user_tokens', cascade='all, delete-orphan'))

    access_token = Column(String(STRING_M_SIZE), nullable=False)
    token_type = Column(String(STRING_XS_SIZE), nullable=False)
    expires_in = Column(Integer)
    refresh_token = Column(String(STRING_M_SIZE))
    scope = Column(String(STRING_L_SIZE))


class GoogleUser(OAuthUser):
    __tablename__ = 'google_user'
    __lation__ = {
        'polymorphic_identity': 'google_user'
    }

    @classmethod
    def login(cls, session:Session, auth:GoogleAuthorizationSchema) -> GoogleUserToken:
        from lation.modules.customer.routers.oauth import google_scheme

        token = google_scheme.request_token(auth)
        id_token_payload_data = google_scheme.decode_id_token(token.id_token)

        google_user = session.query(cls)\
            .filter(cls.account_identifier == id_token_payload_data.sub)\
            .one_or_none()
        if not google_user:
            userinfo_data = google_scheme.request_user_info(token)
            end_user_email = session.query(EndUserEmail).filter(EndUserEmail.email_address == id_token_payload_data.email, EndUserEmail.is_verified == id_token_payload_data.email_verified).one_or_none()
            if not end_user_email:
                end_user = EndUser(end_user_emails=[
                    EndUserEmail(email_address=id_token_payload_data.email,
                                 is_verified=id_token_payload_data.email_verified)
                ])
                session.add(end_user)
            else:
                end_user = end_user_email.end_user
            google_user = cls(end_user=end_user,
                              account_identifier=userinfo_data.sub,
                              profile=userinfo_data.dict())
            session.add(google_user)
        google_user_token = GoogleUserToken(oauth_user=google_user,
                                            access_token=token.access_token,
                                            token_type=token.token_type,
                                            refresh_token=token.refresh_token,
                                            expires_in=token.expires_in,
                                            scope=token.scope,
                                            id_token=token.id_token)
        session.add(google_user_token)
        return google_user_token


class GoogleUserToken(OAuthUserToken, OIDCMixin):
    __tablename__ = 'google_user_token'
    __lation__ = {
        'polymorphic_identity': 'google_user_token'
    }


class LineUser(OAuthUser):
    __tablename__ = 'line_user'
    __lation__ = {
        'polymorphic_identity': 'line_user'
    }

    @classmethod
    def login(cls, session:Session, auth:LineAuthorizationSchema) -> LineUserToken:
        from lation.modules.customer.routers.oauth import line_scheme

        token = line_scheme.request_token(auth)
        id_token_payload_data = line_scheme.decode_id_token(token.id_token)

        line_user = session.query(cls)\
            .filter(cls.account_identifier == id_token_payload_data.sub)\
            .one_or_none()
        if not line_user:
            userinfo_data = line_scheme.request_user_info(token)
            end_user_email = session.query(EndUserEmail).filter(EndUserEmail.email_address == id_token_payload_data.email, EndUserEmail.is_verified == True).one_or_none()
            if not end_user_email:
                end_user = EndUser(end_user_emails=[
                    EndUserEmail(email_address=id_token_payload_data.email,
                                 is_verified=True)
                ])
                session.add(end_user)
            else:
                end_user = end_user_email.end_user
            line_user = cls(end_user=end_user,
                            account_identifier=userinfo_data.userId,
                            profile=userinfo_data.dict())
            session.add(line_user)
        line_user_token = LineUserToken(oauth_user=line_user,
                                        access_token=token.access_token,
                                        token_type=token.token_type,
                                        refresh_token=token.refresh_token,
                                        expires_in=token.expires_in,
                                        scope=token.scope,
                                        id_token=token.id_token)
        session.add(line_user_token)
        return line_user_token


class LineUserToken(OAuthUserToken, OIDCMixin):
    __tablename__ = 'line_user_token'
    __lation__ = {
        'polymorphic_identity': 'line_user_token'
    }
