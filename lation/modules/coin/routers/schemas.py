from typing import Optional

from pydantic import BaseModel


class EndUserBitfinexConfigSchema(BaseModel):
    api_key: Optional[str]
    api_secret: Optional[str]
    config: Optional[dict]

    class Config:
        orm_mode = True
