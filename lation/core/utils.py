import asyncio
import inspect
from functools import wraps


# https://mark1002.github.io/2018/07/31/python-%E5%AF%A6%E7%8F%BE-singleton-%E6%A8%A1%E5%BC%8F/
class SingletonMetaclass(type):

    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance


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

def fallback_empty_kwarg_to_member(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not kwargs.get(name, None):
                instance = args[0]
                kwargs[name] = getattr(instance, name)
            return func(*args, **kwargs)
        return wrapper
    return decorator
