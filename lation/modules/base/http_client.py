import enum
from urllib.parse import urlparse

import requests
from requests.models import Response


class HttpClient:

    class VerbEnum(enum.Enum):
        GET = 'get'
        POST = 'post'

    # https://stackoverflow.com/a/47694595/2443984
    @staticmethod
    def is_valid_url(path_or_url:str) -> bool:
        try:
            result = urlparse(path_or_url)
            return all([result.scheme, result.netloc, result.path])
        except:
            return False

    @staticmethod
    def request_url(http_verb:VerbEnum, url:str, *args, **kwargs) -> Response:
        action = getattr(requests, http_verb.value)
        return action(url, *args, **kwargs)

    def __init__(self, host=None):
        self.host = host

    def get_url(self, path_or_url:str) -> str:
        if HttpClient.is_valid_url(path_or_url):
            return path_or_url
        else:
            if not self.host:
                raise Exception(f'Host cannot be empty when requesting path: {path_or_url}')
            return f'{self.host}{path_or_url}'

    def request(self, http_verb:VerbEnum, path_or_url:str, *args, **kwargs) -> Response:
        url = self.get_url(path_or_url)
        return HttpClient.request_url(http_verb, url, *args, **kwargs)

    def get(self, path_or_url:str, params:dict=None, **kwargs) -> Response:
        return self.request(HttpClient.VerbEnum.GET, path_or_url, params=params, **kwargs)

    def post(self, path_or_url:str, data:dict=None, **kwargs) -> Response:
        return self.request(HttpClient.VerbEnum.POST, path_or_url, data=data, **kwargs)

    def post_json(self, *args, **kwargs) -> dict:
        response = self.post(*args, **kwargs)
        data = response.json()
        return data


class PttWebClient(HttpClient):

    def __init__(self):
        super().__init__(host='https://www.ptt.cc')

    def search(self, board:str, query_str:str) -> Response:
        return self.get(f'/bbs/{board}/search', params={ 'q': query_str })
