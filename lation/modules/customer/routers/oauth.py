from typing import Optional

import requests
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from lation.core.env import get_env
from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.customer.decorators import oauth_login_flow
from lation.modules.customer.models.oauth_user import GoogleUser, GoogleUserToken, LineUser, LineUserToken
from lation.modules.customer.oauth import GoogleScheme, LineScheme
from lation.modules.customer.schemas.oauth import GoogleAuthorizationSchema, LineAuthorizationSchema


HOST = get_env('HOST')
FRONTEND_HOST = get_env('FRONTEND_HOST')
OAUTH_SUCCESS_REDIRECT_URL=f'{FRONTEND_HOST}/auth/result'
OAUTH_FAIL_REDIRECT_URL=f'{FRONTEND_HOST}/auth/result'
OAUTH_GOOGLE_CLIENT_ID = get_env('OAUTH_GOOGLE_CLIENT_ID')
OAUTH_GOOGLE_CLIENT_SECRET = get_env('OAUTH_GOOGLE_CLIENT_SECRET')
OAUTH_LINE_CLIENT_ID = get_env('OAUTH_LINE_CLIENT_ID')
OAUTH_LINE_CLIENT_SECRET = get_env('OAUTH_LINE_CLIENT_SECRET')

google_scheme = GoogleScheme(client_id=OAUTH_GOOGLE_CLIENT_ID,
                             client_secret=OAUTH_GOOGLE_CLIENT_SECRET,
                             redirect_uri=f'{HOST}/auth/google/callback')
line_scheme = LineScheme(client_id=OAUTH_LINE_CLIENT_ID,
                         client_secret=OAUTH_LINE_CLIENT_SECRET,
                         redirect_uri=f'{HOST}/auth/line/callback')
router = APIRouter()


@router.get('/auth/google',
            tags=['oauth_user'],
            summary='Initiate google oauth redirection',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            response_class=RedirectResponse)
def auth_google():
    url = google_scheme.get_authorization_url(scopes=[GoogleScheme.ScopeEnum.EMAIL,
                                                      GoogleScheme.ScopeEnum.OPENID,
                                                      GoogleScheme.ScopeEnum.PROFILE])
    return RedirectResponse(url=url)


@router.get('/auth/google/callback',
            tags=['oauth_user'],
            summary='Callback of google oauth redirect uri',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            response_class=RedirectResponse)
@managed_transaction
@oauth_login_flow(OAUTH_SUCCESS_REDIRECT_URL, OAUTH_FAIL_REDIRECT_URL)
def auth_google_callback(auth:GoogleAuthorizationSchema=Depends(google_scheme.handle_authorization_response),
                         session:Session=Depends(get_session)):
    google_user_token = GoogleUser.login(session, auth)
    login_end_user_token = google_user_token.oauth_user.end_user.login()
    return login_end_user_token


@router.get('/auth/line',
            tags=['oauth_user'],
            summary='Initiate line oauth redirection',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            response_class=RedirectResponse)
def auth_line():
    url = line_scheme.get_authorization_url(scopes=[LineScheme.ScopeEnum.EMAIL,
                                                    LineScheme.ScopeEnum.OPENID,
                                                    LineScheme.ScopeEnum.PROFILE])
    return RedirectResponse(url=url)


@router.get('/auth/line/callback',
            tags=['oauth_user'],
            summary='Callback of line oauth redirect uri',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            response_class=RedirectResponse)
@managed_transaction
@oauth_login_flow(OAUTH_SUCCESS_REDIRECT_URL, OAUTH_FAIL_REDIRECT_URL)
def auth_line_callback(auth:LineAuthorizationSchema=Depends(line_scheme.handle_authorization_response),
                       session:Session=Depends(get_session)):
    line_user_token = LineUser.login(session, auth)
    login_end_user_token = line_user_token.oauth_user.end_user.login()
    return login_end_user_token
