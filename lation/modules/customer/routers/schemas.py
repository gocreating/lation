from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


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

    class Config:
        orm_mode = True

class ProductSchema(BaseModel):
    id: int
    code: str
    name: str
    plans: List[PlanSchema]

    class Config:
        orm_mode = True

class CreateOrderSchema(BaseModel):
    plan_id: int

class OrderPlanSchema(BaseModel):
    id: int
    plan_id: int

    class Config:
        orm_mode = True

class OrderSchema(BaseModel):
    id: int
    order_plans: List[OrderPlanSchema]

    class Config:
        orm_mode = True

class CreateSubscriptionSchema(BaseModel):
    order_plan_id: int

class SubscriptionSchema(BaseModel):
    id: int
    order_plan: OrderPlanSchema

    subscribe_time: datetime
    unsubscribe_time: Optional[datetime] = None

    class Config:
        orm_mode = True
