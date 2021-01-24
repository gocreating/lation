import os

from fastapi import APIRouter

from lation.modules.base_fastapi.routers.schemas import LivenessSchema, Response, StatusEnum, VersionSchema


IMAGE_TAG = os.getenv('IMAGE_TAG')

router = APIRouter()

@router.get('/', tags=['system'], response_model=Response[LivenessSchema])
def liveness():
    return Response[LivenessSchema](status=StatusEnum.SUCCESS)

@router.get('/version', tags=['system'], response_model=Response[VersionSchema])
def version():
    version = IMAGE_TAG if IMAGE_TAG else 'local'
    return Response[VersionSchema](status=StatusEnum.SUCCESS, data=version)
