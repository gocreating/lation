import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lation.core.database import Database
from lation.core.env import get_env

DB_URL = get_env('DB_URL')


class Liveness(BaseModel):
    status: int

class Version(BaseModel):
    status: int
    data: str

class BaseFastAPI(FastAPI):
    def __init__(self):
        super().__init__()
        self.add_middleware(CORSMiddleware,
                            allow_origins=['*'],
                            allow_credentials=True,
                            allow_methods=['*'],
                            allow_headers=['*'])

        @self.get('/', response_model=Liveness)
        def liveness():
            return {'status': 0}

        @self.get('/version', response_model=Version)
        def version():
            IMAGE_TAG = os.getenv('IMAGE_TAG')
            version = IMAGE_TAG if IMAGE_TAG else 'local'
            return {'status': 0, 'data': version}

    def init_database(self):
        @self.on_event('startup')
        async def on_startup():
            self.database = Database(url=DB_URL)

        @self.on_event('shutdown')
        async def on_shutdown():
            pass