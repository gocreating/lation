from pathlib import Path

from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lation.modules.base_fastapi.base_fastapi import BaseFastAPI
from lation.modules.stock.routers import ptt


class StockFastApp(BaseFastAPI):
    def __init__(self):
        super().__init__()
        self.mount('/static', StaticFiles(directory=(Path(__file__).parent / './static').resolve()), name='static')
        self.include_router(ptt.router)

app = StockFastApp()
