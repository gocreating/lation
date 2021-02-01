import os

from fastapi import APIRouter

from lation.core.env import IMAGE_TAG
from lation.modules.base_fastapi.routers.schemas import LivenessSchema, ResponseSchema as Response, StatusEnum, VersionSchema


router = APIRouter()

@router.get('/', tags=['system'], response_model=Response[LivenessSchema])
def liveness():
    return Response[LivenessSchema](status=StatusEnum.SUCCESS)

@router.get('/version', tags=['system'], response_model=Response[VersionSchema])
def version():
    version = IMAGE_TAG if IMAGE_TAG else 'local'
    return Response[VersionSchema](status=StatusEnum.SUCCESS, data=version)
