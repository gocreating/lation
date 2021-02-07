from datetime import timedelta

from fastapi import Response

from lation.modules.base_fastapi.base_fastapi import BaseFastAPI


class CustomerApp(BaseFastAPI):

    ACCESS_TOKEN_COOKIE_KEY = 'ACCESS-TOKEN'
    ACCESS_TOKEN_HEADER_KEY = 'X-ACCESS-TOKEN'

    def __init__(self):
        from lation.modules.customer.routers import oauth, user

        super().__init__()
        super().init_database()
        self.include_router(user.router)
        self.include_router(oauth.router)


def lation_set_access_token(self, token_value:str, **kwargs):
    self.lation_set_cookie(CustomerApp.ACCESS_TOKEN_COOKIE_KEY,
                           value=token_value,
                           max_age=timedelta(days=10).total_seconds(),
                           **kwargs)

def lation_unset_access_token(self):
    self.lation_set_cookie(CustomerApp.ACCESS_TOKEN_COOKIE_KEY,
                           value='',
                           max_age=0)

Response.lation_set_access_token = lation_set_access_token
Response.lation_unset_access_token = lation_unset_access_token
