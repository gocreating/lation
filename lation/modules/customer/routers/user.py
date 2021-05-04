from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response as FastAPIResponse, status
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from lation.core.env import get_env
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.line_api_client import LineAPIClient
from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import login_required, get_current_user
from lation.modules.customer.models.oauth_user import LineUserToken, OAuthUser
from lation.modules.customer.routers.schemas import EndUserSchema, LineFriendshipSchema


LINE_BOT_BASIC_ID = get_env('LINE_BOT_BASIC_ID')

router = APIRouter()

@router.post('/logout',
             tags=['end_user'],
             dependencies=[Depends(login_required)],
             response_model=Response)
def logout(response:FastAPIResponse, end_user=Depends(get_current_user)):
    response.lation_unset_access_token()
    return Response(status=StatusEnum.SUCCESS)

@router.get('/me',
            tags=['end_user'],
            dependencies=[Depends(login_required)],
            response_model=Response[EndUserSchema])
def get_me(end_user=Depends(get_current_user)):
    return Response[EndUserSchema](status=StatusEnum.SUCCESS, data=end_user)

@router.get('/line/friendship',
            tags=['oauth_user'],
            dependencies=[Depends(login_required)],
            response_model=Response[LineFriendshipSchema])
def get_line_user_friendship(end_user=Depends(get_current_user),
                             session:Session=Depends(get_session)):
    line_user_token = session.query(LineUserToken)\
        .join(LineUserToken.oauth_user)\
        .filter(OAuthUser.end_user_id == end_user.id)\
        .order_by(OAuthUser.create_time.desc())\
        .first()
    if not line_user_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Unauthenticated line user')
    if line_user_token.create_time + timedelta(seconds=line_user_token.expires_in) < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Line token expired')
    line_api_client = LineAPIClient(access_token=line_user_token.access_token)
    friendship_status = line_api_client.get_friendship_status()
    return Response[LineFriendshipSchema](
        status=StatusEnum.SUCCESS,
        data=LineFriendshipSchema(is_friend=friendship_status['friendFlag'])
    )

@router.get('/line/add-friend',
            tags=['oauth_user'],
            summary='Initiate line add friend redirection',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            response_class=RedirectResponse)
def get_line_add_friend():
    return RedirectResponse(url=f'https://line.me/R/ti/p/@{LINE_BOT_BASIC_ID}')

@router.get('/line/official-account-qr.png',
            tags=['oauth_user'],
            summary='Initiate line official account qr code image redirection',
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            response_class=RedirectResponse)
def get_line_official_account_qr():
    return RedirectResponse(url=f'https://qr-official.line.me/sid/L/{LINE_BOT_BASIC_ID}.png')
