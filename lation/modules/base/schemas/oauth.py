from typing import Optional

from pydantic import BaseModel


"""
Google
"""

class GoogleAuthorizationSchema(BaseModel):
    state: str
    code: str
    scope: str

# https://developers.google.com/identity/protocols/oauth2/openid-connect#exchangecode
class GoogleTokenSchema(BaseModel):
    access_token: str
    expires_in: int
    id_token: str
    scope: str
    token_type: str
    refresh_token: Optional[str] = None

# https://developers.google.com/identity/protocols/oauth2/openid-connect#obtainuserinfo
class GoogleUserinfoSchema(BaseModel):
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
class LineAuthorizationSchema(BaseModel):
    code: str
    state: str
    friendship_status_changed: bool

# https://developers.line.biz/zh-hant/docs/line-login/integrate-line-login/#response
# https://developers.line.biz/zh-hant/reference/line-login/#issue-token-response
class LineTokenSchema(BaseModel):
    access_token: str
    expires_in: int
    id_token: Optional[str]
    refresh_token: str
    scope: str
    token_type: str

# https://developers.line.biz/zh-hant/reference/line-login/#get-profile-response
class LineUserinfoSchema(BaseModel):
    userId: str
    displayName: str
    pictureUrl: Optional[str]
    statusMessage: Optional[str]
