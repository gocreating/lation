import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter

from lation.modules.base.http_client import HttpClient


router = APIRouter()


class CurrencyClient(HttpClient):

    def get_top_n_symbols(self, n):
        res = self.get('https://coinmarketcap.com/currencies/volume/monthly/')
        soup = BeautifulSoup(res.text, 'html.parser')
        cells = soup.find_all('td', class_='cmc-table__cell--sort-by__symbol')
        symbols = [cell.getText() for cell in cells]
        return symbols[:n]

    # https://www.binance.com/en/markets
    def get_binance_symbols(self):
        data = self.get_json('https://www.binance.com/gateway-api/v1/public/marketing/symbol/list')
        symbols = [datum['name'] for datum in data['data']]
        return symbols

    # https://www.huobi.com/zh-cn/assetintro/
    def get_huobi_symbols(self):
        data = self.get_json('https://www.huobi.com/-/x/pro/v2/beta/common/currencies')
        symbols = [datum['display_name'] for datum in data['data']]
        return symbols

    # https://www.coinbase.com/price/s/listed?resolution=hour&page=2
    def get_coinbase_symbols(self):
        symbols = []
        for page in range(1,6):
            data = self.get_json(f'https://www.coinbase.com/api/v2/assets?filter=all&limit=30&page={page}')
            symbols += [datum['symbol'] for datum in data['data']]
        return symbols

@router.get('/reveal-currency', tags=['experiment'])
async def reveal_currency(top_n:int=50):
    client = CurrencyClient()
    top_n_symbols = client.get_top_n_symbols(top_n)
    binance_symbols = client.get_binance_symbols()
    huobi_symbols = client.get_huobi_symbols()
    coinbase_symbols = client.get_coinbase_symbols()
    return {
        'top_n_symbols': top_n_symbols,
        'binance_symbols': binance_symbols,
        'huobi_symbols': huobi_symbols,
        'coinbase_symbols': coinbase_symbols,
        'top_symbols_not_in_binance': [top_symbol for top_symbol in top_n_symbols if top_symbol not in binance_symbols],
        'top_symbols_not_in_huobi': [top_symbol for top_symbol in top_n_symbols if top_symbol not in huobi_symbols],
        'top_symbols_not_in_coinbase': [top_symbol for top_symbol in top_n_symbols if top_symbol not in coinbase_symbols],
    }
