from datetime import datetime

from sqlalchemy.orm import object_session

from lation.modules.base.models.end_user import EndUser
from lation.modules.base.models.job import Scheduler
from lation.modules.customer.models.oauth_user import LineUser
from lation.modules.customer.models.product import Order, OrderPlan, Plan
from lation.modules.customer.models.subscription import Subscription
from lation.modules.stock.line_api_client import LineAPIClient

@Scheduler.register_cron_job()
def send_ptt_wordcloud_notification(cron_job):
    session = object_session(cron_job)
    line_api_client = LineAPIClient()
    plan = Plan.get_lation_data(session, 'stock.word_cloud_plan_basic')
    line_users = session.query(LineUser)\
        .join(LineUser.end_user)\
        .join(EndUser.orders)\
        .join(Order.order_plans)\
        .join(OrderPlan.subscription)\
        .filter(OrderPlan.plan_id == plan.id)\
        .filter(Subscription.unsubscribe_time == None)\
        .all()
    utc_now = datetime.utcnow()
    today_date_str = utc_now.strftime('%Y-%m-%d')
    for line_user in line_users:
        line_api_client.push_message(line_user.account_identifier, [
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