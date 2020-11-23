from pydantic import BaseModel

from lation.modules.base_fastapi.base_fastapi import BaseFastAPI

class Combo(BaseModel):
    status: int
    data: str

class ComboFastApp(BaseFastAPI):
    def __init__(self):
        super().__init__()

        @self.get('/combo', response_model=Combo)
        def combo():
            return {
                'status': 0,
                'data': 'Welcome to combo api',
            }

app = ComboFastApp()
