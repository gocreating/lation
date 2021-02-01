import inspect


async def call_fn(func, *args, **kwargs):
    if inspect.iscoroutinefunction(func):
        result = await func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)
    return result
