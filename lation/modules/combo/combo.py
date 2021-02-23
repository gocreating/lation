from lation.modules.base_fastapi.base_fastapi import BaseFastAPI
from lation.modules.combo.routers import experiment


class ComboFastApp(BaseFastAPI):

    def __init__(self):
        super().__init__()
        self.include_router(experiment.router)
