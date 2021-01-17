import functools
import inspect

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from lation.modules.base_fastapi.dependencies import get_session

def managed_transaction(func):

    @functools.wraps(func)
    async def wrap_func(*args, session: Session = Depends(get_session), **kwargs):
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(*args, session=session, **kwargs)
            else:
                result = func(*args, session=session, **kwargs)
            session.commit()
        except HTTPException as e:
            session.rollback()
            raise e
        # don't close session here, or you won't be able to response
        return result

    return wrap_func
