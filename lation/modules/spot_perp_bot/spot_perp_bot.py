from lation.modules.base_fastapi.base_fastapi import BaseFastAPI
from lation.modules.spot_perp_bot.routers import ftx


class SpotPerpBotApp(BaseFastAPI):

    def __init__(self):
        super().__init__()
        self.include_router(ftx.router)
