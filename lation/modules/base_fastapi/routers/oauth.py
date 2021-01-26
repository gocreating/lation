from urllib.parse import urlencode
from typing import Optional

import requests
from fastapi import APIRouter, Depends, status
from fastapi.openapi.models import OAuthFlows
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from lation.core.env import get_env
from lation.modules.base.oauth import GoogleScheme, LineScheme
from lation.modules.base.schemas.oauth import GoogleAuthorizationSchema, LineAuthorizationSchema
from lation.modules.base_fastapi.decorators import managed_transaction
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.models.end_user import EndUser
from lation.modules.base_fastapi.models.oauth_user import GoogleUser, GoogleUserToken, LineUser, LineUserToken
from lation.modules.base_fastapi.routers.schemas import ResponseSchema, StatusEnum


HOST = get_env('HOST')
OAUTH_GOOGLE_CLIENT_ID = get_env('OAUTH_GOOGLE_CLIENT_ID')
OAUTH_GOOGLE_CLIENT_SECRET = get_env('OAUTH_GOOGLE_CLIENT_SECRET')
OAUTH_LINE_CLIENT_ID = get_env('OAUTH_LINE_CLIENT_ID')
OAUTH_LINE_CLIENT_SECRET = get_env('OAUTH_LINE_CLIENT_SECRET')

router = APIRouter()
google_scheme = GoogleScheme(client_id=OAUTH_GOOGLE_CLIENT_ID,
                             client_secret=OAUTH_GOOGLE_CLIENT_SECRET,
                             redirect_uri=f'{HOST}/auth/google/callback')
line_scheme = LineScheme(client_id=OAUTH_LINE_CLIENT_ID,
                         client_secret=OAUTH_LINE_CLIENT_SECRET,
                         redirect_uri=f'{HOST}/auth/line/callback')


@router.get('/auth/google',
            tags=['oauth'], summary='Initiate google oauth redirection',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, response_class=RedirectResponse)
def auth_google():
    url = google_scheme.get_authorization_url(scopes=[GoogleScheme.ScopeEnum.EMAIL,
                                                      GoogleScheme.ScopeEnum.OPENID,
                                                      GoogleScheme.ScopeEnum.PROFILE])
    return RedirectResponse(url=url)


@router.get('/auth/google/callback',
            tags=['oauth'], summary='Callback of google oauth redirect uri',
            response_model=ResponseSchema)
@managed_transaction
def auth_google_callback(auth:GoogleAuthorizationSchema=Depends(google_scheme.handle_authorization_response),
                         session:Session=Depends(get_session)):
    google_user = GoogleUser.login(session, auth)
    google_user.end_user.login()
    return ResponseSchema(status=StatusEnum.SUCCESS)


@router.get('/auth/line',
            tags=['oauth'], summary='Initiate line oauth redirection',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT, response_class=RedirectResponse)
def auth_line():
    url = line_scheme.get_authorization_url(scopes=[LineScheme.ScopeEnum.EMAIL,
                                                    LineScheme.ScopeEnum.OPENID,
                                                    LineScheme.ScopeEnum.PROFILE])
    return RedirectResponse(url=url)


@router.get('/auth/line/callback',
            tags=['oauth'], summary='Callback of line oauth redirect uri',
            response_model=ResponseSchema)
@managed_transaction
def auth_line_callback(auth:LineAuthorizationSchema=Depends(line_scheme.handle_authorization_response),
                       session:Session=Depends(get_session)):
    line_user = LineUser.login(session, auth)
    line_user.end_user.login()
    return ResponseSchema(status=StatusEnum.SUCCESS)
