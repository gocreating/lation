import os

from fastapi import APIRouter

from lation.modules.base_fastapi.routers import schemas

IMAGE_TAG = os.getenv('IMAGE_TAG')

router = APIRouter()


@router.get('/', tags=['system'], response_model=schemas.Liveness)
def liveness():
    return {'status': 0}

@router.get('/version', tags=['system'], response_model=schemas.Version)
def version():    
    version = IMAGE_TAG if IMAGE_TAG else 'local'
    return {'status': 0, 'data': version}