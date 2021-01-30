from typing import Optional

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from lation.core.database.database import Database
from lation.core.env import DEV, get_env
from lation.modules.base_fastapi.routers import system


DB_URL = get_env('DB_URL')


class BaseFastAPI(FastAPI):

    def __init__(self):
        super().__init__()
        self.add_middleware(CORSMiddleware,
                            allow_origins=['*'],
                            allow_credentials=True,
                            allow_methods=['*'],
                            allow_headers=['*'])
        self.include_router(system.router)

    def init_database(self):
        @self.on_event('startup')
        async def on_startup():
            self.state.database = Database(url=DB_URL)

        @self.on_event('shutdown')
        async def on_shutdown():
            if self.state.database:
                self.state.database.dispose()


def lation_set_cookie(self, *args, secure:Optional[bool]=None, httponly:Optional[bool]=True, **kwargs):
    if secure is None:
        secure = True if not DEV else False
    self.set_cookie(*args, secure=secure, httponly=httponly, **kwargs)

Response.lation_set_cookie = lation_set_cookie
