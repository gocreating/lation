from lation.core.env import get_env
from lation.modules.base.http_client import HttpClient, Response


LINE_CHANNEL_ACCESS_TOKEN = get_env('LINE_CHANNEL_ACCESS_TOKEN')

class LineAPIClient(HttpClient):

    def __init__(self, access_token=None):
        super().__init__(host='https://api.line.me')
        if not access_token:
            access_token = LINE_CHANNEL_ACCESS_TOKEN
        self.access_token = access_token

    # https://developers.line.biz/zh-hant/docs/line-login/link-a-bot/#use-social-api
    def get_friendship_status(self) -> dict:
        return self.get_json('/friendship/v1/status',
                              headers={'Authorization': f'Bearer {self.access_token}'})


    def push_message(self, to:str, messages) -> dict:
        return self.post_json('/v2/bot/message/push',
                              headers={'Authorization': f'Bearer {self.access_token}'},
                              json={'to': to, 'messages': messages})
