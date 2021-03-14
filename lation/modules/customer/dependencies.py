from typing import Optional

from fastapi import Depends, HTTPException, Request, Response, Security, status
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader
from sqlalchemy.orm import Session

from lation.modules.base.models.end_user import EndUser, EndUserToken
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.customer.customer import CustomerApp
from lation.modules.customer.models.platform import Platform


# https://medium.com/data-rebels/fastapi-authentication-revisited-enabling-api-key-authentication-122dc5975680
access_token_cookie_scheme = APIKeyCookie(scheme_name='Access Token Cookie Scheme',
                                          name=CustomerApp.ACCESS_TOKEN_COOKIE_KEY,
                                          auto_error=False)
access_token_header_scheme = APIKeyHeader(scheme_name='Access Token Header Scheme',
                                          name=CustomerApp.ACCESS_TOKEN_HEADER_KEY,
                                          auto_error=False)
async def get_access_token(access_token_cookie:Optional[str]=Security(access_token_cookie_scheme),
                           access_token_header:Optional[str]=Security(access_token_header_scheme)) -> str:
    if access_token_cookie:
        return access_token_cookie
    elif access_token_header:
        return access_token_header
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Access token required')

async def login_required(request:Request, access_token:str=Depends(get_access_token), session:Session=Depends(get_session)):
    end_user_token = session.query(EndUserToken)\
        .filter(EndUserToken.value == access_token, EndUserToken.is_active == True)\
        .one_or_none()
    if not end_user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid access token')
    request.state.end_user_token = end_user_token

async def get_current_user(request:Request) -> EndUser:
    end_user_token = request.state.end_user_token
    return end_user_token.end_user

async def get_current_platform(session:Session=Depends(get_session)) -> Platform:
    return session.query(Platform).one()
