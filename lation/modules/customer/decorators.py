import functools
from urllib.parse import quote_plus

from fastapi import Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from lation.core.utils import call_fn
from lation.modules.base.models.end_user import EndUserToken
from lation.modules.base_fastapi.dependencies import get_session
from lation.modules.base_fastapi.routers.schemas import StatusEnum


def managed_oauth_flow(success_url:str, fail_url:str):

    def decorator(func):

        @functools.wraps(func)
        async def wrap_func(*args, session:Session=Depends(get_session), **kwargs):
            try:
                end_user_token = await call_fn(func, *args, session=session, **kwargs)
                if not isinstance(end_user_token, EndUserToken):
                    raise Exception('The path operation decorated with `@managed_oauth_flow` should return value of type `EndUserToken`')
                session.commit()
                response = RedirectResponse(f'{success_url}?status={StatusEnum.SUCCESS}')
                response.lation_set_access_token(end_user_token.value)
                return response
            except Exception as e:
                # TODO: narrow down catch scopes
                session.rollback()
                return RedirectResponse(f'{fail_url}?status={StatusEnum.FAILED}&error={quote_plus(str(e))}')

        return wrap_func

    return decorator
