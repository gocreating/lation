from pathlib import Path

from fastapi import APIRouter

from lation.modules.base.models.notification import Notification


router = APIRouter()

@router.get('/send-smtp', tags=['experiment'])
async def push_smtp_notification():
    notification = Notification()
    notification.send_email((Path(__file__).parent / '../data/email_template.html').resolve())
    return None
