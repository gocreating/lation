from datetime import datetime, timedelta

class Cache():
    def set(self, key, value):
        raise NotImplementedError

    def get(self, key):
        raise NotImplementedError

    def evict(self, key):
        raise NotImplementedError

    def __del__(self):
        raise NotImplementedError

class MemoryCache(Cache):
    def __init__(self, ttl: timedelta = None):
        self._cache: dict = {}
        self._ttl = ttl

    def set(self, key, value):
        self._cache[key] = (value, datetime.utcnow())

    def get(self, key):
        value, set_time = self._cache.get(key, (None, None))
        if set_time == None:
            return None
        if self._ttl != None and set_time + self._ttl < datetime.utcnow():
            return None
        return value

    def evict(self, key):
        del self._cache[key]

    def __del__(self):
        for cache_key in self._cache.keys():
            self.evict[cache_key]

class CacheRegistry():
    cache_map = {}

    @classmethod
    def register(cls, key, cache):
        cls.cache_map[key] = cache

    @classmethod
    def get(cls, key):
        return cls.cache_map[key]

    @classmethod
    def unregister(cls, key):
        del cls.cache_map[key]

    @classmethod
    def unregister_all(cls):
        for cache_key in cls.cache_map.keys():
            cls.unregister(cache_key)