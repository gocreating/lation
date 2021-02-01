from lation.core.env import get_env
from lation.modules.base.http_client import HttpClient, Response


LINE_CHANNEL_ACCESS_TOKEN = get_env('LINE_CHANNEL_ACCESS_TOKEN')

class LineAPIClient(HttpClient):

    def __init__(self, channel_access_token=None):
        super().__init__(host='https://api.line.me')
        if not channel_access_token:
            channel_access_token = LINE_CHANNEL_ACCESS_TOKEN
        self.channel_access_token = channel_access_token

    def push_message(self, to:str, messages) -> dict:
        return self.post_json('/v2/bot/message/push',
                              headers={'Authorization': f'Bearer {self.channel_access_token}'},
                              json={'to': to, 'messages': messages})
