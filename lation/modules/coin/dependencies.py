from fastapi import Depends, HTTPException, status

from lation.modules.coin.bitfinex_api_client import BitfinexAPIClient
from lation.modules.customer.dependencies import login_required, get_current_user


async def get_bitfinex_api_client(end_user=Depends(get_current_user)) -> BitfinexAPIClient:
    end_user_bitfinex_config = end_user.end_user_bitfinex_config
    if not end_user_bitfinex_config:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Bitfinex config not found')
    if not end_user_bitfinex_config.api_key or not end_user_bitfinex_config.api_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid bitfinex credential config')
    bitfinex_api_client = BitfinexAPIClient(api_key=end_user_bitfinex_config.api_key,
                                            api_secret=end_user_bitfinex_config.api_secret)
    return bitfinex_api_client
