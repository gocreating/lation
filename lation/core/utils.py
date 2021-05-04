import asyncio
import enum
import inspect
import time
from datetime import datetime, timedelta
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

class RateLimiter:

    def __init__(self, max_calls: int, period_in_seconds: int):
        self.max_calls = max_calls
        self.period_in_seconds = period_in_seconds
        self.called_datetimes = []
        self.queued_datetimes = []

    def min_waiting_seconds(self) -> int:
        utcnow = datetime.utcnow()
        expiry = utcnow - timedelta(seconds=self.period_in_seconds)
        self.called_datetimes = [called_datetime for called_datetime in self.called_datetimes if called_datetime >= expiry]
        self.queued_datetimes = [queued_datetime for queued_datetime in self.queued_datetimes if queued_datetime >= utcnow]

        if len(self.called_datetimes) + len(self.queued_datetimes) < self.max_calls:
            return 0

        if len(self.called_datetimes) > 0:
            oldest_called_datetime = self.called_datetimes[0]
        elif len(self.queued_datetimes) > 0:
            oldest_called_datetime = self.queued_datetimes[0]
        elapsed_seconds = (utcnow - oldest_called_datetime).total_seconds()
        return self.period_in_seconds - elapsed_seconds

    def wait_strategy(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            waiting_seconds = self.min_waiting_seconds()
            if waiting_seconds > 0:
                self.queued_datetimes.append(datetime.utcnow() + timedelta(seconds=waiting_seconds))
                time.sleep(waiting_seconds)
            self.called_datetimes.append(datetime.utcnow())
            return func(*args, **kwargs)
        return wrapper

    def drop_strategy(self, func):
        raise NotImplementedError

    def raise_strategy(self, func):
        raise NotImplementedError

def extend_enum(target_enum, source_enum):
    target_dict = {e.name: e.value for e in target_enum}
    source_dict = {e.name: e.value for e in source_enum}
    target_dict.update(source_dict)
    return enum.Enum(target_enum.__name__, target_dict)
