from bs4 import BeautifulSoup
from fastapi import APIRouter
from lation.modules.base.ptt_client import PttClient

router = APIRouter()


def get_first_matched_link(html):
    soup = BeautifulSoup(html, 'html.parser')
    link = soup.find_all('div', class_='title')[0].find('a').attrs['href']
    return link

def get_push_contents(html):
    soup = BeautifulSoup(html, 'html.parser')
    push_contents = soup.find_all('span', class_='push-content')
    return push_contents

@router.get('/ptt/latest-push-contents', tags=['stock'])
async def ptt_crawler():
    ptt_client = PttClient()
    res = ptt_client.search('Stock', '盤中閒聊')
    target_link = get_first_matched_link(res.text)
    res = ptt_client.get(target_link)
    push_contents = get_push_contents(res.text)
    return [push_content.getText()[2:] for push_content in push_contents]
