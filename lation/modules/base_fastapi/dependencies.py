from typing import Iterator

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from lation.core.env import DEV


def get_session(request: Request) -> Iterator[Session]:
    request.state.session = request.app.state.database.get_session()
    try:
        yield request.state.session
    finally:
        request.state.session.close()


class Cookie:

    ACCESS_TOKEN_KEY = 'ACCESS-TOKEN'

    def __init__(self, request:Request, response:Response):
        self.request = request
        self.response = response

    def set(self, *args, secure=None, httponly=True, **kwargs):
        if secure is None:
            secure = True if not DEV else False
        self.response.set_cookie(*args, secure=secure, httponly=httponly, **kwargs)

    def set_access_token(self, token_value:str, **kwargs):
        cls = self.__class__
        self.set(cls.ACCESS_TOKEN_KEY, value=token_value, **kwargs)
