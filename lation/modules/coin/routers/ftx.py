from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from lation.modules.coin.ftx_api_client import FTXRestAPIClient


router = APIRouter()

@router.get('/ftx/test', tags=['ftx'])
async def test():
    ftx_rest_api_client = FTXRestAPIClient('xxx', 'yyy')
    balances = ftx_rest_api_client.get_balances()
    return balances
