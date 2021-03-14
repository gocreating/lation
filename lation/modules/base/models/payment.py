from lation.core.orm import Base, SingleTableInheritanceMixin


class PaymentGateway(Base, SingleTableInheritanceMixin):
    __tablename__ = 'payment_gateway'

    def create_order(self, *args, **kwargs):
        raise NotImplementedError

    def get_payment_page_content(self, *args, **kwargs):
        raise NotImplementedError
