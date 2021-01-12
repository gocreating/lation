from typing import Callable

from fastapi import Depends, Request

def get_session(request: Request):
    return request.app.database.get_session

def session(get_session: Callable = Depends(get_session)):
    return get_session()