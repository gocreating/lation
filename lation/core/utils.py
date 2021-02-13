import asyncio
import inspect
from functools import wraps


async def call_fn(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        result = await func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)
    return result

# https://github.com/pallets/click/issues/85#issuecomment-503464628
def coro(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    return wrapper