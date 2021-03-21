from sqlalchemy import Column

from lation.core.database.types import STRING_XS_SIZE, String
from lation.core.orm import Base


class Currency(Base):
    __tablename__ = 'currency'

    code = Column(String(STRING_XS_SIZE), nullable=False)
