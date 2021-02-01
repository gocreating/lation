from fastapi import APIRouter, Depends, Response as FastAPIResponse

from lation.modules.base_fastapi.routers.schemas import ResponseSchema as Response, StatusEnum
from lation.modules.customer.dependencies import login_required, get_current_user
from lation.modules.customer.routers.schemas import UserSchema


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
            response_model=Response[UserSchema])
def get_me(end_user=Depends(get_current_user)):
    return Response[UserSchema](status=StatusEnum.SUCCESS, data=end_user)
