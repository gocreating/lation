from sqlalchemy import event

from lation.modules.customer.models.oauth_user import LineUser
from lation.modules.customer.models.subscription import Subscription


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
