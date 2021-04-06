from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from lation.modules.customer.models.product import Order


class CurrencySchema(BaseModel):
    code: Optional[str] = None

    class Config:
        orm_mode = True

class PaymentGatewaySchema(BaseModel):
    id: int

    class Config:
        orm_mode = True

class EndUserSchema(BaseModel):
    id: int

    class Config:
        orm_mode = True

class LineFriendshipSchema(BaseModel):
    is_friend: bool

class PlanSchema(BaseModel):
    id: int
    code: str
    name: str
    plan_prices: List[PlanPriceSchema]
    product: Optional[ProductSchema]
    sequence: Optional[int]

    class Config:
        orm_mode = True

class PlanPriceSchema(BaseModel):
    standard_price_amount: float
    currency: CurrencySchema

    class Config:
        orm_mode = True

class ProductSchema(BaseModel):
    id: int
    code: str
    name: str
    plans: List[PlanSchema]
    sequence: Optional[int]

    class Config:
        orm_mode = True

class PaymentSchema(BaseModel):
    id: int
    billed_amount: float
    billed_currency: CurrencySchema
    create_time: datetime

    class Config:
        orm_mode = True

class CreateOrderSchema(BaseModel):
    plan_id: int

class PrimitiveOrderSchema(BaseModel):
    id: int
    state: Order.StateEnum

    class Config:
        orm_mode = True

class OrderSchema(PrimitiveOrderSchema):
    order_plans: List[OrderPlanSchema]
    payment: Optional[PaymentSchema]

class OrderPlanSchema(BaseModel):
    id: int
    plan: PlanSchema
    order: OrderSchema

    class Config:
        orm_mode = True

class CreateSubscriptionSchema(BaseModel):
    order_plan_id: int

class SubscriptionSchema(BaseModel):
    id: int
    order_plan: OrderPlanSchema

    subscribe_time: datetime
    due_time: Optional[datetime] = None
    unsubscribe_time: Optional[datetime] = None

    class Config:
        orm_mode = True

# for circular schema reference
OrderSchema.update_forward_refs()
PlanSchema.update_forward_refs()
