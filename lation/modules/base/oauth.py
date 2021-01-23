import enum
import random
from typing import List
from urllib.parse import urlencode

import requests

from lation.modules.base.http_client import HttpClient

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
                 client_id:str, client_secret:str,
                 authorization_endpoint:str, token_endpoint:str,
                 redirect_uri:str, userinfo_endpoint:str=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.redirect_uri = redirect_uri
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

    def request_token(self, code:str) -> dict:
        data = HttpClient.post_url_json(self.token_endpoint, data={
            'grant_type': OAuth2.GrantTypeEnum.AUTHORIZATION_CODE.value,
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        return data

    def request_resource(self, url:str, token_data:dict) -> dict:
        token_type, access_token = token_data['token_type'], token_data['access_token']
        data = HttpClient.post_url_json(url, headers={
            'Authorization': f'{token_type} {access_token}',
        })
        return data

    def request_userinfo(self, token_data:dict) -> dict:
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
                                      state:str=None, code:str=None, scope:str=None) -> dict:
        return {
            'state': state,
            'code': code,
            'scope': scope,
        }

    def request_token(self, code:str) -> dict:
        data = super().request_token(code)
        return {
            'access_token': data['access_token'],
            'token_type': data['token_type'],
            'refresh_token': data['refresh_token'],
            'expires_in': data['expires_in'],
            'scope': data['scope'],
        }

    def request_userinfo(self, token_data:dict) -> dict:
        data = super().request_userinfo(token_data)
        return {
            'sub': data['sub'],
            'name': data['name'],
            'given_name': data['given_name'],
            'family_name': data['family_name'],
            'picture': data['picture'],
            'email': data['email'],
            'email_verified': data['email_verified'],
            'locale': data['locale'],
        }


class LineScheme(AuthorizationCodeProvider):

    class ScopeEnum(enum.Enum):
        OPENID = (0, 'openid')
        PROFILE = (1, 'profile')
        EMAIL = (2, 'email')

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
                                      error:str=None, error_description:str=None) -> dict:
        if code:
            # will receive `state`, `code`, and `friendship_status_changed`
            return {
                'code': code,
                'friendship_status_changed': friendship_status_changed,
            }
        elif error:
            # will receive `state`, `error`, and `error_description`
            raise Exception(error)

    def request_token(self, code:str) -> dict:
        data = super().request_token(code)
        if 'error' in data:
            raise Exception(data['error'])
        return {
            'access_token': data['access_token'],
            'token_type': data['token_type'],
            'refresh_token': data['refresh_token'],
            'expires_in': data['expires_in'],
            'scope': data['scope'],
            # 'id_token': data['id_token'],
        }

    def request_userinfo(self, token_data:dict) -> dict:
        data = super().request_userinfo(token_data)
        return {
            'userId': data['userId'],
            'displayName': data['displayName'],
            'pictureUrl': data['pictureUrl'],
        }
