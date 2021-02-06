import datetime

from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base, declared_attr, has_inherited_table
from sqlalchemy.schema import MetaData
from sqlalchemy.sql import func

from lation.core.database.database import Database
from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, DateTime, Integer, String
from lation.core.env import get_env


APP = get_env('APP')

class JoinedTableInheritanceMixin:

    model = Column(String(STRING_S_SIZE), comment='Polymorphic on model')

    @declared_attr
    def __mapper_args__(cls):
        if not cls.__lation__ or not cls.__lation__.get('polymorphic_identity'):
            raise Exception(f'Model `{cls.__name__}` should define attribute `__lation__.polymorphic_identity` due to joined injeritance')
        return {
            'polymorphic_on': cls.model,
            'polymorphic_identity': cls.__lation__['polymorphic_identity'],
            # https://docs.sqlalchemy.org/en/13/orm/inheritance_loading.html#setting-with-polymorphic-at-mapper-configuration-time
            # allowing eager loading of attributes from subclass tables
            'with_polymorphic': '*',
        }


class SingleTableInheritanceMixin:

    __lation__ = {
        'polymorphic_identity': 'default'
    }

    discriminator = Column(String(STRING_S_SIZE), index=True, comment='Polymorphic on discriminator')

    @declared_attr
    def __mapper_args__(cls):
        if has_inherited_table(cls):
            if SingleTableInheritanceMixin in cls.mro():
                top_class = cls.__bases__[0]
                if cls.__tablename__ != top_class.__tablename__:
                    raise Exception(f'Model `{cls.__name__}` should not define attribute `__tablename__` due to single heritance')
                polymorphic_identity = cls.__lation__.get('polymorphic_identity')
                if polymorphic_identity == top_class.__lation__.get('polymorphic_identity'):
                    raise Exception(f'Model `{cls.__name__}` should define attribute `__lation__.polymorphic_identity` with non-duplicate value. Duplicate value `{polymorphic_identity}` was detected.')
        return {
            'polymorphic_on': cls.discriminator,
            'polymorphic_identity': cls.__lation__['polymorphic_identity'],
        }


# https://docs.sqlalchemy.org/en/14/orm/declarative_mixins.html#augmenting-the-base
class BaseClass:

    # https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/api.html#sqlalchemy.ext.declarative.declared_attr.cascading
    @declared_attr.cascading
    def id(cls):
        if has_inherited_table(cls):
            if JoinedTableInheritanceMixin in cls.mro():
                for base in cls.__bases__:
                    if hasattr(base, 'id'):
                        return Column(Integer, ForeignKey(base.id), primary_key=True, autoincrement=False)
            if SingleTableInheritanceMixin in cls.mro():
                return None
        return Column(Integer, primary_key=True)

    lation_id = Column(String(STRING_M_SIZE), nullable=True, index=True)
    created_at = Column(DateTime, index=True, server_default=func.now())
    updated_at = Column(DateTime, index=True, server_default=func.now(), onupdate=func.now())

Base = declarative_base(cls=BaseClass, metadata=Database.get_metadata())
