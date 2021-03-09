import csv
import os
import random
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter
from fastapi.responses import FileResponse

from lation.modules.base.http_client import HttpClient


router = APIRouter()


class SymbolClient(HttpClient):

    def get_top_monthly_volume_symbols(self, n):
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

    # https://www.okex.com/hk/markets/coin-list
    def get_okex_symbols(self):
        data = self.get_json('https://www.okex.com/v2/support/info/announce/listProject')
        symbols = [datum['project'] for datum in data['data']['list']]
        return symbols

    # https://ftx.com/markets
    def get_ftx_symbols(self):
        data = self.get_json('https://ftx.com/api/coins')
        symbols = [datum['id'] for datum in data['result']]
        return symbols


@router.get('/symbols/exchange-insight/download', tags=['experiment'])
async def download_exchange_insight_symbols(top_n:int=50):
    client = SymbolClient()
    top_symbols = client.get_top_monthly_volume_symbols(top_n)
    binance_symbols = client.get_binance_symbols()
    huobi_symbols = client.get_huobi_symbols()
    coinbase_symbols = client.get_coinbase_symbols()
    okex_symbols = client.get_okex_symbols()
    ftx_symbols = client.get_ftx_symbols()

    datetime_str = datetime.utcnow().strftime("%Y_%m_%d_%H_%M_%S")
    file_path = os.path.join('./', f'exchange_insight_{datetime_str}_random_{random.randint(1, 1000)}.csv')
    with open(file_path, 'w', newline='') as output_file:
        writer = csv.DictWriter(output_file, fieldnames=['symbol', 'rank_by_30d_volume', 'binance', 'huobi', 'coinbase', 'okex', 'ftx'])
        writer.writeheader()
        for i, symbol in enumerate(top_symbols):
            writer.writerow({
                'symbol': symbol,
                'rank_by_30d_volume': i + 1,
                'binance': 'yes' if symbol in binance_symbols else '',
                'huobi': 'yes' if symbol in huobi_symbols else '',
                'coinbase': 'yes' if symbol in coinbase_symbols else '',
                'okex': 'yes' if symbol in okex_symbols else '',
                'ftx': 'yes' if symbol in ftx_symbols else '',
            })
    return FileResponse(file_path, filename=f'exchange_insight_{datetime_str}.csv')
