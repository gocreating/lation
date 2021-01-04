import requests

class PttClient():
    host = 'https://www.ptt.cc'

    @classmethod
    def get(cls, url, **kwargs):
        return requests.get(f'{cls.host}{url}', **kwargs)

    def search(self, board, query_str):
        res = self.get(f'/bbs/{board}/search', params={ 'q': query_str })
        return res