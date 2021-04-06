from datetime import datetime

from sqlalchemy import event
from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser
from lation.modules.base.models.job import Scheduler, JobProducer
from lation.modules.customer.models.oauth_user import LineUser
from lation.modules.customer.models.product import Order, OrderPlan, Plan
from lation.modules.customer.models.subscription import Subscription
from lation.modules.stock.line_api_client import LineAPIClient


@event.listens_for(Subscription, 'after_insert')
def receive_after_insert(mapper, connection, subscription):
    order_plan = subscription.order_plan
    plan = order_plan.plan
    if plan.code == 'BASIC':
        end_user = order_plan.order.end_user
        line_user = next((oauth_user for oauth_user in end_user.oauth_users if isinstance(oauth_user, LineUser)), None)
        line_user.push_message([
            {
                'type': 'text',
                'text': '歡迎使用股票精靈，目前最新股市風向雲如附圖',
            },
            {
                'type': 'image',
                'originalContentUrl': 'https://stock-api.lation.app:5555/static/latest-push-content-cut-words.png',
                'previewImageUrl': 'https://stock.lation.app/logo.png',
            }
        ])


@Scheduler.register_cron_job()
def send_ptt_wordcloud_notification(cron_job):
    session = object_session(cron_job)
    line_api_client = LineAPIClient()
    plan = Plan.get_lation_data(session, 'stock.word_cloud_plan_basic')
    line_users = session.query(LineUser)\
        .join(LineUser.end_user)\
        .join(EndUser.orders)\
        .join(Order.order_plans)\
        .join(OrderPlan.subscriptions)\
        .filter(OrderPlan.plan_id == plan.id)\
        .filter(Subscription.unsubscribe_time == None)\
        .all()
    utc_now = datetime.utcnow()
    today_date_str = utc_now.strftime('%Y-%m-%d')
    for line_user in line_users:
        JobProducer(line_user).push_message([
            {
                'type': 'text',
                'text': f'{today_date_str} 股市風向雲如附圖，股票精靈感謝您的訂閱！',
            },
            {
                'type': 'image',
                'originalContentUrl': 'https://stock-api.lation.app:5555/static/latest-push-content-cut-words.png',
                'previewImageUrl': 'https://stock.lation.app/logo.png',
            },
        ])
