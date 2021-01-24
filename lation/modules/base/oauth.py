import enum
import random
from typing import List
from urllib.parse import urlencode

import jwt
import requests
from pydantic import BaseModel

from lation.modules.base.http_client import HttpClient
from lation.modules.base.schemas.oauth import \
    GoogleAuthorizationSchema, GoogleTokenSchema, GoogleIdTokenPayloadSchema, GoogleUserinfoSchema, \
    LineAuthorizationSchema, LineTokenSchema, LineIdTokenPayloadSchema, LineUserinfoSchema

class OAuth2:

    class ResponseTypeEnum(enum.Enum):
        CODE = 'code'
        TOKEN = 'token'

    class GrantTypeEnum(enum.Enum):
        AUTHORIZATION_CODE = 'authorization_code'

    # https://stackoverflow.com/questions/5590170/what-is-the-standard-method-for-generating-a-nonce-in-python
    def generate_nonce(self, length:int=8) -> str:
        return ''.join([str(random.randint(0, 9)) for i in range(length)])

    def make_scope(self, scopes:List[enum.Enum]) -> str:
        sorted_scopes = sorted(scopes, key=lambda s: s.value[0])
        return ' '.join([s.value[1] for s in sorted_scopes])


class AuthorizationCodeProvider(OAuth2):

    def __init__(self,
                 client_id:str, client_secret:str, redirect_uri:str,
                 authorization_endpoint:str=None, token_endpoint:str=None, userinfo_endpoint:str=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.userinfo_endpoint = userinfo_endpoint

    def get_authorization_url(self, scope:str=None, state:str=None, **kwargs) -> str:
        query = {
            'client_id': self.client_id,
            'response_type': OAuth2.ResponseTypeEnum.CODE.value,
            'scope': scope,
            'state': state if state else 'OAuth2 flow powered by https://lation.app',
            'redirect_uri': self.redirect_uri,
            'nonce': self.generate_nonce(),
        }
        query.update(kwargs)
        return f'{self.authorization_endpoint}?{urlencode(query)}'

    def handle_authorization_response(self, *args, **kwargs):
        raise NotImplementedError

    def request_token_by_code(self, code:str) -> dict:
        data = HttpClient.post_url_json(self.token_endpoint, data={
            'grant_type': OAuth2.GrantTypeEnum.AUTHORIZATION_CODE.value,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        # TODO: check status code
        if 'error' in data:
            raise Exception(data['error'])
        return data

    def decode_id_token(self, id_token:str) -> BaseModel:
        raise NotImplementedError

    def request_resource(self, url:str, token_data:BaseModel) -> dict:
        data = HttpClient.post_url_json(url, headers={
            'Authorization': f'{token_data.token_type} {token_data.access_token}',
        })
        return data

    def request_userinfo(self, token_data:BaseModel) -> dict:
        return self.request_resource(self.userinfo_endpoint, token_data)


class GoogleScheme(AuthorizationCodeProvider):

    # must begin with the openid value and then include the profile value, the email value, or both
    class ScopeEnum(enum.Enum):
        OPENID = (0, 'openid')
        PROFILE = (1, 'profile')
        EMAIL = (2, 'email')

    class AccessTypeEnum(enum.Enum):
        OFFLINE = 'offline'
        ONLINE = 'online'

    def __init__(self, client_id:str, client_secret:str, redirect_uri:str):
        super().__init__(client_id=client_id,
                         client_secret=client_secret,
                         redirect_uri=redirect_uri,
                         authorization_endpoint='https://accounts.google.com/o/oauth2/v2/auth',
                         token_endpoint='https://oauth2.googleapis.com/token',
                         userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo') # alternative: 'https://www.googleapis.com/oauth2/v3/userinfo'

    def get_authorization_url(self,
                              *args,
                              scope:str=None,
                              scopes:List[ScopeEnum]=None,
                              access_type:AccessTypeEnum=None,
                              **kwargs) -> str:
        if scopes:
            scope = self.make_scope(scopes)
        if not access_type:
            access_type = GoogleScheme.AccessTypeEnum.OFFLINE
        return super().get_authorization_url(*args, **kwargs, scope=scope, access_type=access_type.value)

    def handle_authorization_response(self,
                                      state:str=None, code:str=None, scope:str=None,
                                      error:str=None) -> GoogleAuthorizationSchema:
        if not code:
            raise Exception(error)
        return GoogleAuthorizationSchema(state=state, code=code, scope=scope)

    def request_token(self, auth_data:GoogleAuthorizationSchema) -> GoogleTokenSchema:
        dict_data = super().request_token_by_code(auth_data.code)
        return GoogleTokenSchema(**dict_data)

    def decode_id_token(self, id_token:str) -> GoogleIdTokenPayloadSchema:
        payload = jwt.decode(id_token, algorithm='HS256', options={'verify_signature': False})
        return GoogleIdTokenPayloadSchema(**payload)

    def request_userinfo(self, token_data:GoogleTokenSchema) -> GoogleUserinfoSchema:
        dict_data = super().request_userinfo(token_data)
        return GoogleUserinfoSchema(**dict_data)


class LineScheme(AuthorizationCodeProvider):

    class ScopeEnum(enum.Enum):
        OPENID = (0, 'openid')
        PROFILE = (1, 'profile')
        EMAIL = (2, 'email')

    def __init__(self, client_id:str, client_secret:str, redirect_uri:str):
        super().__init__(client_id=client_id,
                         client_secret=client_secret,
                         redirect_uri=redirect_uri,
                         authorization_endpoint='https://access.line.me/oauth2/v2.1/authorize',
                         token_endpoint='https://api.line.me/oauth2/v2.1/token',
                         userinfo_endpoint='https://api.line.me/v2/profile')

    def get_authorization_url(self,
                              *args,
                              scope:str=None,
                              scopes:List[ScopeEnum]=None,
                              **kwargs) -> str:
        if scopes:
            scope = self.make_scope(scopes)
        return super().get_authorization_url(*args, scope=scope, **kwargs)

    def handle_authorization_response(self,
                                      state:str=None,
                                      code:str=None, friendship_status_changed:bool=False,
                                      error:str=None, error_description:str=None) -> LineAuthorizationSchema:
        if not code:
            raise Exception(f'{error}: {error_description}')
        return LineAuthorizationSchema(code=code, state=state, friendship_status_changed=friendship_status_changed)

    def request_token(self, auth_data:LineAuthorizationSchema) -> LineTokenSchema:
        dict_data = super().request_token_by_code(auth_data.code)
        return LineTokenSchema(**dict_data)

    def decode_id_token(self, id_token:str) -> LineIdTokenPayloadSchema:
        payload = jwt.decode(id_token, algorithm='HS256', options={'verify_signature': False})
        return LineIdTokenPayloadSchema(**payload)

    def request_userinfo(self, token_data:LineTokenSchema) -> LineUserinfoSchema:
        dict_data = super().request_userinfo(token_data)
        return LineUserinfoSchema(**dict_data)
