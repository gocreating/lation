from pathlib import Path

from fastapi import APIRouter

from lation.modules.base.models.notification import Notification
from lation.modules.stock.line_api_client import LineAPIClient


router = APIRouter()

@router.get('/send-smtp', tags=['experiment'])
async def push_smtp_notification():
    notification = Notification()
    notification.send_email((Path(__file__).parent / '../data/email_template.html').resolve())
    return None

@router.get('/send-line-notification', tags=['experiment'])
async def push_line_notification():
    line_api_client = LineAPIClient()
    res_data = line_api_client.push_message('U5abfe9090acd8357516e26604a3606b6', [{
        'type': 'image',
        'originalContentUrl': 'https://stock-api.lation.app:5555/static/latest-push-content-cut-words.png',
        'previewImageUrl': 'https://stock.lation.app/logo.png',
    }])
    res_data = line_api_client.push_message('U5abfe9090acd8357516e26604a3606b6', [{
        'type': 'text',
        'text': '嗨，Lation Stock 使用者您好',
    }])
    return None
