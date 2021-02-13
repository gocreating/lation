from pathlib import Path

import jieba
from bs4 import BeautifulSoup
from wordcloud import WordCloud

from lation.modules.base.models.job import Scheduler
from lation.modules.stock.ptt_web_client import PttWebClient
from lation.modules.stock.routers.ptt import PTT_PUSH_CONTENT_CACHE_KEY


jieba.set_dictionary((Path(__file__).parent / '../data/dict.txt.big.txt').resolve())


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
    custom_stop_words_file_path = (Path(__file__).parent / '../data/custom_stop_words.txt').resolve()
    stop_words = (
        [word.strip() for word in open(stop_words_file_path, 'r', encoding='utf-8').readlines()] +
        [word.strip() for word in open(custom_stop_words_file_path, 'r', encoding='utf-8').readlines()] +
        [' ']
    )
    cut_words = []
    for line in lines:
        cut_words += [cut_word for cut_word in jieba.cut(line, cut_all=False) if cut_word not in stop_words]
    return cut_words

def get_ptt_push_content_cut_words(board: str, search: str):
    ptt_web_client = PttWebClient()
    res = ptt_web_client.search(board, search)
    target_link = get_first_matched_link(res.text)
    res = ptt_web_client.get(target_link)
    push_contents = get_push_contents(res.text)
    lines = [push_content.getText()[2:] for push_content in push_contents]
    cut_words = get_cut_words(lines)
    return cut_words

@Scheduler.register_cron_job(execute_once_initialized=True)
def generate_ptt_wordcloud(cron_job):
    ptt_push_content_cut_words = get_ptt_push_content_cut_words('Stock', '盤中閒聊')
    wc = WordCloud(scale=3,
                   background_color='white',
                   font_path=str((Path(__file__).parent / '../data/TaipeiSansTCBeta-Regular.ttf').resolve()))\
        .generate(' '.join(ptt_push_content_cut_words))
    wc.to_file((Path(__file__).parent / '../static/latest-push-content-cut-words.png').resolve())
