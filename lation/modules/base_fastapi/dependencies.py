from fastapi import Depends, Request

def get_session(request: Request):
    request.state.session = request.app.state.database.get_session()
    try:
        yield request.state.session
    finally:
        request.state.session.close()
