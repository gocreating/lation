from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lation.core.database.database import Database
from lation.core.env import get_env
from lation.modules.base_fastapi.routers import system

DB_URL = get_env('DB_URL')

global_get_session = None

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
            global global_get_session
            database = Database(url=DB_URL)
            global_get_session = database.get_session
            self.state.database = database

        @self.on_event('shutdown')
        async def on_shutdown():
            if self.state.database:
                self.state.database.dispose()
