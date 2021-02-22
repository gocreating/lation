from typing import List

from lation.modules.customer.models.oauth_user import LineUser
from lation.modules.stock.line_api_client import LineAPIClient


def push_message(self, messages:List[dict]):
    line_api_client = LineAPIClient()
    line_api_client.push_message(self.account_identifier, messages)

LineUser.push_message = push_message
