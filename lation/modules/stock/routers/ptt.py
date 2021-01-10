from pathlib import Path

import jieba
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends
from wordcloud import WordCloud

from lation.modules.base.cache import CacheRegistry, MemoryCache
from lation.modules.base.models.notification import Notification
from lation.modules.base.ptt_client import PttClient

router = APIRouter()

jieba.set_dictionary((Path(__file__).parent / '../data/dict.txt.big.txt').resolve())

def memory_cache():
    from lation.modules.stock.app import StockFastApp
    return CacheRegistry.get(StockFastApp.CACHE_KEY)

def get_first_matched_link(html):
    soup = BeautifulSoup(html, 'html.parser')
    link = soup.find_all('div', class_='title')[0].find('a').attrs['href']
    return link

def get_push_contents(html):
    soup = BeautifulSoup(html, 'html.parser')
    push_contents = soup.find_all('span', class_='push-content')
    return push_contents

def get_cut_words(lines):
    stop_words_file_path = (Path(__file__).parent / '../data/stop_words.txt').resolve()
    stop_words = [word.strip() for word in open(stop_words_file_path, 'r', encoding='utf-8').readlines()] + [' ']
    cut_words = []
    for line in lines:
        cut_words += [cut_word for cut_word in jieba.cut(line, cut_all=False) if cut_word not in stop_words]
    return cut_words

@router.get('/ptt/latest-push-content-cut-words', tags=['stock'])
async def ptt_crawler(board: str, search: str, cache: MemoryCache = Depends(memory_cache)):
    cached_response = cache.get('ptt')
    if cached_response != None:
        return cached_response

    ptt_client = PttClient()
    res = ptt_client.search(board, search)
    target_link = get_first_matched_link(res.text)
    res = ptt_client.get(target_link)
    push_contents = get_push_contents(res.text)
    lines = [push_content.getText()[2:] for push_content in push_contents]
    cut_words = get_cut_words(lines)
    wc = WordCloud(scale=3,
                   background_color='white',
                   font_path=str((Path(__file__).parent / '../data/TaipeiSansTCBeta-Regular.ttf').resolve())).generate(' '.join(cut_words))
    wc.to_file((Path(__file__).parent / '../static/latest-push-content-cut-words.png').resolve())
    cache.set('ptt', cut_words)
    return cut_words

@router.get('/test-smtp', tags=['misc'])
async def test_smtp():
    notification = Notification()
    notification.send_email((Path(__file__).parent / '../data/email_template.html').resolve())
    return None