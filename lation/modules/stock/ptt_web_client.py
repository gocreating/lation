from lation.modules.base.http_client import HttpClient, Response


class PttWebClient(HttpClient):

    def __init__(self):
        super().__init__(host='https://www.ptt.cc')

    def search(self, board:str, query_str:str) -> Response:
        return self.get(f'/bbs/{board}/search', params={ 'q': query_str })
