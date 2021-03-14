from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import backref, relationship

from lation.core.database.types import STRING_S_SIZE, STRING_XS_SIZE, DateTime, Float, Integer, String
from lation.core.orm import Base, Machine, MachineMixin


class Product(Base):
    __tablename__ = 'product'

    code = Column(String(STRING_XS_SIZE), nullable=False, comment='Product code')
    name = Column(String(STRING_S_SIZE), nullable=False, comment='Product name')

    currency_id = Column(Integer, ForeignKey('currency.id'), index=True)
    currency = relationship('Currency', foreign_keys=[currency_id])


class Plan(Base):
    __tablename__ = 'plan'

    code = Column(String(STRING_XS_SIZE), nullable=False, comment='Plan code')
    name = Column(String(STRING_S_SIZE), nullable=False, comment='Plan name')

    product_id = Column(Integer, ForeignKey('product.id'), index=True)
    product = relationship('Product', foreign_keys=[product_id], backref=backref('plans', cascade='all, delete-orphan'))

    standard_price_amount = Column(Float)


class Order(Base, MachineMixin):
    __tablename__ = 'order'

    machine = Machine(
        initial=lambda s: s.draft,
        states=lambda s: {
            s.draft: {
                'on': {
                    'initiate_charge': s.pending_payment,
                },
            },
            s.pending_payment: {
                'on': {
                    'charge_success': s.effective,
                    'charge_fail': s.payment_failed,
                },
            },
            s.effective: {
                'on': {
                    'expire': s.expired,
                },
            },
            s.expired: {},
            s.payment_failed: {},
        }
    )

    end_user_id = Column(Integer, ForeignKey('end_user.id'), index=True)
    end_user = relationship('EndUser', foreign_keys=[end_user_id], backref=backref('orders'))

    purchase_time = Column(DateTime)

    @machine.bind_action
    def initiate_charge(self):
        pass


class OrderPlan(Base):
    __tablename__ = 'order_plan'

    order_id = Column(Integer, ForeignKey('order.id'), index=True)
    order = relationship('Order', foreign_keys=[order_id], backref=backref('order_plans'))

    plan_id = Column(Integer, ForeignKey('plan.id'), index=True)
    plan = relationship('Plan', foreign_keys=[plan_id])
