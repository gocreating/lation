from __future__ import annotations
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class FtxArbitrageStrategyConfig(BaseModel):

    class LeverageDiffToQuoteAmountRule(BaseModel):
        gte_leverage_diff: float
        lt_leverage_diff: float
        quote_amount: Decimal

    class AlarmConfig(BaseModel):
        enabled: bool = True
        gt_leverage: float = 17.5

    class IncreasePairConfig(BaseModel):
        enabled: bool = True
        lt_leverage: float = 11.0
        gt_spread_rate: float = 0.003,
        max_balance_rate: float = 0.2
        leverage_diff_to_quote_amount_rules: List[FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule] = []

    class AlwaysIncreasePairConfig(BaseModel):
        enabled: bool = True
        gt_spread_rate: float = 0.0065
        quote_amount: Decimal = Decimal('30')

    class DecreasePairConfig(BaseModel):
        enabled: bool = True
        gt_leverage: float = 17.0
        lt_spread_rate: float = -0.001
        leverage_diff_to_quote_amount_rules: List[FtxArbitrageStrategyConfig.LeverageDiffToQuoteAmountRule] = []

    class AlwaysDecreasePairConfig(BaseModel):
        enabled: bool = True
        lt_spread_rate: float = -0.001
        quote_amount: Decimal = Decimal('30')

    class ClosePairConfig(BaseModel):
        gt_leverage: float = 20.0

    class GarbageCollectConfig(BaseModel):
        enabled: bool = False
        lt_spread_rate: float = 0.001

    alarm: Optional[FtxArbitrageStrategyConfig.AlarmConfig]
    increase_pair: Optional[FtxArbitrageStrategyConfig.IncreasePairConfig]
    always_increase_pair: Optional[FtxArbitrageStrategyConfig.AlwaysIncreasePairConfig]
    decrease_pair: Optional[FtxArbitrageStrategyConfig.DecreasePairConfig]
    always_decrease_pair: Optional[FtxArbitrageStrategyConfig.AlwaysDecreasePairConfig]
    close_pair: Optional[FtxArbitrageStrategyConfig.ClosePairConfig]
    garbage_collect: Optional[FtxArbitrageStrategyConfig.GarbageCollectConfig]

FtxArbitrageStrategyConfig.IncreasePairConfig.update_forward_refs()
FtxArbitrageStrategyConfig.DecreasePairConfig.update_forward_refs()
FtxArbitrageStrategyConfig.update_forward_refs()
