from functools import lru_cache, wraps
import time


def ttl_lru_cache(ttl: int, maxsize: int):
    """
    Quick and dirty implementation of an LRU cache that also allows objects to expire.
    It works by wrapping your function in the standard functools lru cache and silently
    adding a time offset parameter to cause all calls to result in cache misses every
    `ttl` seconds.
    """
    def function_wrapper(f):
        @lru_cache(maxsize=maxsize)
        def lru_inner(offset, *args, **kwargs):
            return f(*args, **kwargs)

        @wraps(f)
        def inner(*args, **kwargs):
            return lru_inner(time.monotonic()//ttl, *args, **kwargs)

        return inner
    return function_wrapper
