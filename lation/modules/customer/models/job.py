from sqlalchemy.orm import object_session

from lation.modules.base.models.job import JobProducer, Scheduler
from lation.modules.base.models.payment import PaymentGateway


@Scheduler.register_cron_job()
def sync_payment(cron_job):
    session = object_session(cron_job)
    payment_gateways = session.query(PaymentGateway).all()
    for payment_gateway in payment_gateways:
        JobProducer(payment_gateway).sync_payment()
    return f'payment_gateways={payment_gateways}'
