from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lation.core.database.database import Database
from lation.core.env import get_env
from lation.modules.base_fastapi.routers import oauth, system


DB_URL = get_env('DB_URL')


class BaseFastAPI(FastAPI):
    def __init__(self):
        super().__init__()
        self.add_middleware(CORSMiddleware,
                            allow_origins=['*'],
                            allow_credentials=True,
                            allow_methods=['*'],
                            allow_headers=['*'])
        self.include_router(oauth.router)
        self.include_router(system.router)

    def init_database(self):
        @self.on_event('startup')
        async def on_startup():
            self.state.database = Database(url=DB_URL)

        @self.on_event('shutdown')
        async def on_shutdown():
            if self.state.database:
                self.state.database.dispose()
