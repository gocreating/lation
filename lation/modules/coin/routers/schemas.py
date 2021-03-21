import enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class BitfinexFundingSymbol(str, enum.Enum):
    USD = 'fUSD'

class BitfinexSymbolFundingAmountStrategy(BaseModel):
    hold_amount: float = 0
    min_per_offer_amount: float = 50
    max_per_offer_amount: float = 500

class BitfinexSymbolFundingRateStrategy(BaseModel):
    min_per_offer_rate: float = 0
    max_per_offer_rate: float = 2555

class BitfinexSymbolFundingRateToPeriodRule(BaseModel):
    gte_rate: float
    lt_rate: float
    period: int

class BitfinexSymbolFundingStrategy(BaseModel):
    enabled: bool = False
    amount_strategy: BitfinexSymbolFundingAmountStrategy
    rate_strategy: BitfinexSymbolFundingRateStrategy
    rate_to_period_rules: List[BitfinexSymbolFundingRateToPeriodRule]

class BitfinexFundingStrategy(BaseModel):
    enabled: bool = False
    symbol_strategy: Dict[str, BitfinexSymbolFundingStrategy]

class EndUserBitfinexConfigSchema(BaseModel):
    api_key: Optional[str]
    api_secret: Optional[str]
    funding_strategy: Optional[BitfinexFundingStrategy]

    class Config:
        orm_mode = True

class BitfinexMetricsSchema(BaseModel):
    funding_market_recommended_ask_rate: float
