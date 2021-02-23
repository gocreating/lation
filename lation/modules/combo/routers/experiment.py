import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter

from lation.modules.base.http_client import HttpClient


router = APIRouter()


class CurrencyClient(HttpClient):

    def get_top_200_symbols(self):
        res = self.get('https://coinmarketcap.com/currencies/volume/monthly/')
        soup = BeautifulSoup(res.text, 'html.parser')
        cells = soup.find_all('td', class_='cmc-table__cell--sort-by__symbol')
        symbols = [cell.getText() for cell in cells]
        return symbols

    # https://www.binance.com/en/markets
    def get_binance_symbols(self):
        data = self.get_json('https://www.binance.com/gateway-api/v1/public/marketing/symbol/list')
        symbols = [datum['name'] for datum in data['data']]
        return symbols

@router.get('/reveal-currency', tags=['experiment'])
async def reveal_currency():
    client = CurrencyClient()
    top_200_symbols = client.get_top_200_symbols()
    binance_symbols = client.get_binance_symbols()
    return {
        'top_200_symbols': top_200_symbols,
        'binance_symbols': binance_symbols,
        'top_symbols_not_in_binance': [top_symbol for top_symbol in top_symbols if top_symbol not in binance_symbols],
    }
