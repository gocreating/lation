from datetime import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import DateTime, Integer
from lation.core.orm import Base


class Subscription(Base):
    __tablename__ = 'subscription'

    order_plan_id = Column(Integer, ForeignKey('order_plan.id'), index=True)
    order_plan = relationship('OrderPlan', foreign_keys=[order_plan_id], backref=backref('subscription', uselist=False))

    subscribe_time = Column(DateTime)
    unsubscribe_time = Column(DateTime)

    def unsubscribe(self):
        self.unsubscribe_time = datetime.utcnow()
