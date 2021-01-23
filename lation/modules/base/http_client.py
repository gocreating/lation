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

    @staticmethod
    def get_url(url:str, *args, params:dict=None, **kwargs) -> Response:
        return HttpClient.request_url(HttpClient.VerbEnum.GET, url, *args, params=params, **kwargs)

    @staticmethod
    def post_url(url:str, *args, data:dict=None, **kwargs) -> Response:
        return HttpClient.request_url(HttpClient.VerbEnum.POST, url, *args, data=data, **kwargs)

    @staticmethod
    def post_url_json(url:str, *args, **kwargs) -> dict:
        res = HttpClient.post_url(url, *args, **kwargs)
        data = res.json()
        return data

    def __init__(self, host=None):
        self.host = host

    def render_url(self, path_or_url:str) -> str:
        if HttpClient.is_valid_url(path_or_url):
            return path_or_url
        else:
            if not self.host:
                raise Exception(f'Host cannot be empty when requesting path: {path_or_url}')
            return f'{self.host}{path_or_url}'

    def get(self, path_or_url:str, *args, **kwargs) -> Response:
        return HttpClient.get_url(self.render_url(path_or_url), *args, **kwargs)

    def post(self, path_or_url:str, *args, **kwargs) -> Response:
        return HttpClient.post_url(self.render_url(path_or_url), *args, **kwargs)

    def post_json(self, path_or_url:str, *args, **kwargs) -> dict:
        return HttpClient.post_url_json(self.render_url(path_or_url), *args, **kwargs)

Response = Response
