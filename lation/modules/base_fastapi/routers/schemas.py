import enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


DataT = TypeVar('DataT')

class StatusEnum(int, enum.Enum):
    SUCCESS = 0
    FAILED = 1

class Response(GenericModel, Generic[DataT]):
    status: StatusEnum
    data: Optional[DataT]

class LivenessSchema(BaseModel):
    pass

class VersionSchema(BaseModel):
    __root__: str
