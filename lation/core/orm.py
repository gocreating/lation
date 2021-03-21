from typing import Any, Callable, Dict, Literal
import datetime
import enum

from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.declarative import declarative_base, declared_attr, has_inherited_table
from sqlalchemy.schema import MetaData
from sqlalchemy.sql import func

from lation.core.database.database import Database
from lation.core.database.types import STRING_M_SIZE, STRING_S_SIZE, STRING_XS_SIZE, DateTime, Integer, String
from lation.core.env import get_env


APP = get_env('APP')


class MachineStateFactory:

    def __init__(self):
        self.__machine_states__ = set()

    def __getattr__(self, name):
        if name.startswith('_'):
            return self.__getattribute__(name)
        machine_state = MachineState(name)
        self.__machine_states__.add(machine_state)
        return machine_state


class MachineState:

    def __init__(self, name):
        self.name = name.upper()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Machine:

    def __init__(self,
                 initial:Callable[[MachineStateFactory],MachineState],
                 states:Callable[
                     [MachineStateFactory],
                     Dict[MachineState, Dict[Literal['on'], Dict[str, MachineState]]]
                 ]):
        machine_state_factory = MachineStateFactory()
        self.initial_machine_state = initial(machine_state_factory)
        self.states = states(machine_state_factory)
        self.state_names = [machine_state.name for machine_state in machine_state_factory.__machine_states__]

    def bind_action(self, func):
        action_name = func.__name__
        def wrapped_func(*args, **kwargs):
            result = func(*args, **kwargs)
            current_state_name = args[0].state
            if not current_state_name:
                raise Exception('Current state cannot be None')
            current_machine_state = MachineState(current_state_name)
            current_state_transition_map = self.states.get(current_machine_state, {}).get('on')
            if not current_state_transition_map:
                raise Exception(f'Invalid state transition. Trasition definition for state `{current_state_name}` is not found.')
            next_machine_state = current_state_transition_map.get(action_name)
            if not next_machine_state:
                raise Exception(f'Invalid state transition. Cannot apply action `{action_name}` to state `{current_state_name}`')
            args[0].state = next_machine_state.name
            return result
        return wrapped_func


class MachineMixin:

    @declared_attr
    def StateEnum(cls):
        return enum.Enum('StateEnum', { state_name: state_name for state_name in cls.machine.state_names })

    @declared_attr
    def state(cls):
        return Column(String(STRING_XS_SIZE), default=cls.machine.initial_machine_state.name)


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
    create_time = Column(DateTime, index=True, server_default=func.now())
    update_time = Column(DateTime, index=True, server_default=func.now(), onupdate=func.now())

    @classmethod
    def get_lation_data(cls, session, lation_id):
        return session.query(cls).filter_by(lation_id=lation_id).one()


Base = declarative_base(cls=BaseClass, metadata=Database.get_metadata())
