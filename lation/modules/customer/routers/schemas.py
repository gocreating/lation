from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int

    class Config:
        orm_mode = True
