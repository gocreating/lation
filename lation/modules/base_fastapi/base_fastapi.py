import os

from fastapi import FastAPI
from pydantic import BaseModel

class Liveness(BaseModel):
    status: int

class Version(BaseModel):
    status: int
    data: str

class BaseFastAPI(FastAPI):
    def __init__(self):
        super().__init__()

        @self.get('/', response_model=Liveness)
        def liveness():
            return {'status': 0}

        @self.get('/version', response_model=Version)
        def version():
            IMAGE_TAG = os.getenv('IMAGE_TAG')
            version = IMAGE_TAG if IMAGE_TAG else 'local'
            return {'status': 0, 'data': version}
