from fastapi import FastAPI
from pydantic import BaseModel

class Liveness(BaseModel):
    status: int

class BaseFastAPI(FastAPI):
    def __init__(self):
        super().__init__()

        @self.get('/', response_model=Liveness)
        def liveness():
            return {'status': 0}
