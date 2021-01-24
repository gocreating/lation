from typing import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

def get_session(request: Request) -> Iterator[Session]:
    request.state.session = request.app.state.database.get_session()
    try:
        yield request.state.session
    finally:
        request.state.session.close()
