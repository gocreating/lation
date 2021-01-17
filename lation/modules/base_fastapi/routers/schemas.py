from pydantic import BaseModel

class Liveness(BaseModel):
    status: int

class Version(BaseModel):
    status: int
    data: str
