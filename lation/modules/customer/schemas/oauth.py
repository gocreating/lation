import enum
from typing import List, Literal, Optional

from pydantic import BaseModel


"""
Base OAuth
"""

class BaseAuthorizationSchema(BaseModel):
    code: str
    state: Optional[str]

class BaseTokenSchema(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int]
    refresh_token: Optional[str]
    scope: Optional[str]


"""
Base OIDC
"""

# https://openid.net/specs/openid-connect-core-1_0.html#TokenResponse
class BaseIdTokenSchema(BaseModel):
    id_token: str

# https://openid.net/specs/openid-connect-core-1_0.html#IDToken
class BaseIdTokenPayloadSchema(BaseModel):
    iss: str
    sub: str
    aud: str
    exp: int
    iat: int

    auth_time: Optional[int]
    nonce: Optional[str]
    acr: Optional[str]
    amr: Optional[List[str]]
    azp: Optional[str]

    at_hash: Optional[str]
    c_hash: Optional[str]

class BaseUserInfoSchema(BaseModel):
    pass


"""
Google
"""

# https://developers.google.com/identity/protocols/oauth2/openid-connect#confirmxsrftoken
class GoogleAuthorizationSchema(BaseAuthorizationSchema):
    scope: Optional[str]

# https://developers.google.com/identity/protocols/oauth2/openid-connect#exchangecode
class GoogleTokenSchema(BaseTokenSchema, BaseIdTokenSchema):
    pass

# https://developers.google.com/identity/protocols/oauth2/openid-connect#an-id-tokens-payload
class GoogleIdTokenPayloadSchema(BaseIdTokenPayloadSchema):
    iss: Literal['https://accounts.google.com']

    email: Optional[str]
    email_verified: Optional[bool]
    family_name: Optional[str]
    given_name: Optional[str]
    hd: Optional[str]
    locale: Optional[str]
    name: Optional[str]
    picture: Optional[str]
    profile: Optional[str]

# https://developers.google.com/identity/protocols/oauth2/openid-connect#obtainuserinfo
class GoogleUserInfoSchema(BaseUserInfoSchema):
    sub: str
    name: str
    given_name: str
    family_name: str
    picture: str
    email: str
    email_verified: bool
    locale: str


"""
Line
"""

# https://developers.line.biz/zh-hant/docs/line-login/integrate-line-login/#receiving-the-authorization-code
class LineAuthorizationSchema(BaseAuthorizationSchema):
    friendship_status_changed: Optional[bool]

# https://developers.line.biz/zh-hant/docs/line-login/integrate-line-login/#response
# https://developers.line.biz/zh-hant/reference/line-login/#issue-token-response
class LineTokenSchema(BaseTokenSchema, BaseIdTokenSchema):
    id_token: Optional[str]

# https://developers.line.biz/zh-hant/docs/line-login/integrate-line-login/#payload
class LineIdTokenPayloadSchema(BaseIdTokenPayloadSchema):
    iss: Literal['https://access.line.me']
    amr: List[Literal['pwd', 'lineautologin', 'lineqr', 'linesso']]

    name: Optional[str]
    picture: Optional[str]
    email: Optional[str]

# https://developers.line.biz/zh-hant/reference/line-login/#get-profile-response
class LineUserInfoSchema(BaseUserInfoSchema):
    userId: str
    displayName: str
    pictureUrl: Optional[str]
    statusMessage: Optional[str]
