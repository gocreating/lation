from lation.modules.base.cache import CacheRegistry, MemoryCache


async def get_memory_cache() -> MemoryCache:
    from lation.modules.stock.stock import StockFastApp
    return CacheRegistry.get(StockFastApp.CACHE_KEY)