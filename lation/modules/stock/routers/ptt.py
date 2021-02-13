from fastapi import APIRouter, Depends

from lation.modules.stock.dependencies import get_memory_cache


PTT_PUSH_CONTENT_CACHE_KEY = 'latest-push-content-cut-words'

router = APIRouter()

@router.get('/ptt/latest-push-content-cut-words', tags=['stock'])
async def ptt_crawler(board: str, search: str, cache = Depends(get_memory_cache)):
    cached_response = cache.get(PTT_PUSH_CONTENT_CACHE_KEY)
    if cached_response != None:
        return cached_response

    from lation.modules.stock.models.job import get_ptt_push_content_cut_words
    ptt_push_content_cut_words = get_ptt_push_content_cut_words(board, search)
    cache.set(PTT_PUSH_CONTENT_CACHE_KEY, ptt_push_content_cut_words)
    return ptt_push_content_cut_words
