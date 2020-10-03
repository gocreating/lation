from sqlalchemy import Column, Integer, DateTime

class ComboMixin(object):
    id = Column(Integer, primary_key=True)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
