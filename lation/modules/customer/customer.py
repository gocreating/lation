from datetime import timedelta
from pathlib import Path

from fastapi import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lation.modules.base.cache import CacheRegistry, MemoryCache
from lation.modules.base_fastapi.base_fastapi import BaseFastAPI


class CustomerApp(BaseFastAPI):

    ACCESS_TOKEN_COOKIE_KEY = 'ACCESS-TOKEN'

    def __init__(self):
        from lation.modules.customer.routers import oauth, user

        super().__init__()
        super().init_database()
        self.include_router(user.router)
        self.include_router(oauth.router)


def lation_set_access_token(self, token_value:str, **kwargs):
    self.lation_set_cookie(CustomerApp.ACCESS_TOKEN_COOKIE_KEY, value=token_value, **kwargs)

Response.lation_set_access_token = lation_set_access_token
