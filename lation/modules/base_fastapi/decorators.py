import functools
import inspect
from urllib.parse import quote_plus

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import StatusEnum


async def exec(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        result = await func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)
    return result


def managed_transaction(func):

    @functools.wraps(func)
    async def wrap_func(*args, session: Session = Depends(get_session), **kwargs):
        try:
            result = await exec(func, *args, session=session, **kwargs)
            session.commit()
        except HTTPException as e:
            session.rollback()
            raise e
        except Exception as e:
            session.rollback()
            raise e
        # don't close session here, or you won't be able to response
        return result

    return wrap_func


def managed_oauth_flow(success_url, fail_url):

    def decorator(func):

        @functools.wraps(func)
        async def wrap_func(*args, session: Session = Depends(get_session), **kwargs):
            try:
                await exec(func, *args, session=session, **kwargs)
                session.commit()
                return RedirectResponse(url=f'{success_url}?status={StatusEnum.SUCCESS}')
            except Exception as e: # TODO: narrow down catch scopes
                session.rollback()
                return RedirectResponse(url=f'{fail_url}?status={StatusEnum.FAILED}&error={quote_plus(str(e))}')

        return wrap_func

    return decorator
