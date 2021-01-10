import datetime

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from lation.core.env import get_env

APP = get_env('APP')

# https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html#augmenting-the-base
class BaseClass(object):
    __table_args__ = {'schema': APP}

    id =  Column(Integer, primary_key=True)
    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())

Base = declarative_base(cls=BaseClass)