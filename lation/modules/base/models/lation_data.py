from sqlalchemy import Column

from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, Integer, String
from lation.core.orm import Base


class LationData(Base):
    __tablename__ = 'lation_data'

    model = Column(String(STRING_S_SIZE), index=True)
    model_lation_id = Column(String(STRING_M_SIZE), index=True)
    model_id = Column(Integer)
