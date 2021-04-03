from datetime import datetime
from typing import Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref, object_session, relationship

from lation.core.database.types import STRING_S_SIZE, STRING_XS_SIZE, DateTime, Integer, Numeric, String
from lation.core.env import get_env
from lation.core.orm import Base, Machine, MachineMixin
from lation.modules.base.models.currency import Currency
from lation.modules.base.models.payment import Payment, PaymentGateway, PaymentGatewayTrade, PaymentItem


APP = get_env('APP')

class Product(Base):
    __tablename__ = 'product'

    code = Column(String(STRING_XS_SIZE), nullable=False, comment='Product code')
    name = Column(String(STRING_S_SIZE), nullable=False, comment='Product name')

    max_end_user_effective_order_count = Column(Integer)


class Plan(Base):
    __tablename__ = 'plan'

    code = Column(String(STRING_XS_SIZE), nullable=False, comment='Plan code')
    name = Column(String(STRING_S_SIZE), nullable=False, comment='Plan name')

    product_id = Column(Integer, ForeignKey('product.id'), index=True)
    product = relationship('Product', foreign_keys=[product_id], backref=backref('plans', cascade='all, delete-orphan'))

    max_end_user_effective_order_count = Column(Integer)


class PlanPrice(Base):
    __tablename__ = 'plan_price'

    plan_id = Column(Integer, ForeignKey('plan.id'), index=True)
    plan = relationship('Plan', foreign_keys=[plan_id], backref=backref('plan_prices'))

    standard_price_amount = Column(Numeric)

    currency_id = Column(Integer, ForeignKey('currency.id'), index=True)
    currency = relationship('Currency', foreign_keys=[currency_id])


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

    initiate_charge_time = Column(DateTime)
    charge_success_time = Column(DateTime)
    charge_fail_time = Column(DateTime)

    payment_id = Column(Integer, ForeignKey('payment.id'), index=True)
    payment = relationship('Payment', foreign_keys=[payment_id], backref=backref('order', uselist=False))

    plans = association_proxy('order_plans', 'plan')

    def get_total_price_amount(self, currency: Currency) -> float:
        acc_price_amount = 0
        for plan in self.plans:
            for plan_price in plan.plan_prices:
                if not plan_price.currency.code or plan_price.currency == currency:
                    acc_price_amount += plan_price.standard_price_amount
                    break
            else:
                raise Exception(f'Plan `{plan.code}` does not have pricing in currency `{currency.code}`')
        return acc_price_amount

    @machine.bind_action
    def initiate_charge(self):
        self.initiate_charge_time = datetime.utcnow()

    def charge(self, payment_gateway: PaymentGateway) -> Optional[str]:
        self.initiate_charge()
        primary_currency = payment_gateway.prioritized_currencies[0]
        total_price_amount = self.get_total_price_amount(primary_currency)
        if total_price_amount > 0:
            payment_gateway_trade = payment_gateway.create_trade(primary_currency)
            self.payment_gateway_trades.append(payment_gateway_trade)
            payment_gateway_order = payment_gateway.create_order(
                payment_gateway_trade,
                description='Here is your order from lation.app',
                item_name=','.join([f'{plan.product.name}: {plan.name}' for plan in self.plans]),
                amount=total_price_amount,
                state={
                    'lation_app': APP,
                    'order_id': self.id,
                }
            )
            content = payment_gateway.get_payment_page_content(payment_gateway_order)
            return content
        else:
            self.charge_success()

    @machine.bind_action
    def charge_success(self, payment_gateway_trade: Optional[PaymentGatewayTrade] = None):
        self.charge_success_time = datetime.utcnow()

        if payment_gateway_trade:
            billed_amount = payment_gateway_trade.trade_amt
            billed_currency = payment_gateway_trade.currency
        else:
            session = object_session(self)
            billed_amount = 0
            billed_currency = Currency.get_lation_data(session, 'base.currency_none')

        payment_items = []
        for plan in self.plans:
            plan_price = next((plan_price for plan_price in plan.plan_prices if plan_price.currency == billed_currency), None)
            payment_item = PaymentItem(item_name=plan.code,
                                       billed_amount=plan_price.standard_price_amount,
                                       billed_currency=plan_price.currency)
            payment_items.append(payment_item)
        self.payment = Payment(payment_gateway_trade=payment_gateway_trade,
                               billed_amount=billed_amount,
                               billed_currency=billed_currency,
                               payment_items=payment_items)
        self.after_order_charge_sucess()

    def after_order_charge_sucess(self):
        pass

    @machine.bind_action
    def charge_fail(self):
        self.charge_fail_time = datetime.utcnow()


class OrderPlan(Base):
    __tablename__ = 'order_plan'

    order_id = Column(Integer, ForeignKey('order.id'), index=True)
    order = relationship('Order', foreign_keys=[order_id], backref=backref('order_plans'))

    plan_id = Column(Integer, ForeignKey('plan.id'), index=True)
    plan = relationship('Plan', foreign_keys=[plan_id])
