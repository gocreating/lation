from typing import Optional

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from lation.modules.base.models.end_user import EndUser, EndUserToken
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.customer.customer import CustomerApp


def login_required(request:Request, session:Session=Depends(get_session)):
    access_token = request.cookies.get(CustomerApp.ACCESS_TOKEN_COOKIE_KEY)
    if not access_token:
        raise HTTPException(status_code=401, detail='Access token required')
    end_user_token = session.query(EndUserToken)\
        .filter(EndUserToken.value == access_token, EndUserToken.is_active == True)\
        .one_or_none()
    if not end_user_token:
        raise HTTPException(status_code=401, detail='Invalid access token')
    request.state.end_user_token = end_user_token

def get_current_user(request:Request) -> EndUser:
    end_user_token = request.state.end_user_token
    return end_user_token.end_user
