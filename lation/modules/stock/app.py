from datetime import timedelta
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lation.modules.base.cache import CacheRegistry, MemoryCache
from lation.modules.customer.customer import CustomerApp
from lation.modules.stock.routers import experiment, ptt


class StockFastApp(CustomerApp):
    CACHE_KEY = 'API_RESPONSE_MEMORY_CACHE'

    def __init__(self):
        super().__init__()
        self.mount('/static', StaticFiles(directory=(Path(__file__).parent / './static').resolve()), name='static')
        self.include_router(ptt.router)
        self.include_router(experiment.router)
        self.init_cache_registry()

    def init_cache_registry(self):
        cls = self.__class__

        @self.on_event('startup')
        async def on_startup():
            CacheRegistry.register(cls.CACHE_KEY, MemoryCache(ttl=timedelta(minutes=15)))

        @self.on_event('shutdown')
        async def on_shutdown():
            CacheRegistry.unregister_all()

app = StockFastApp()
