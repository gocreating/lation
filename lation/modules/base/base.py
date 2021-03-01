from lation.modules.base.models.job import CoroutineScheduler


class BaseLationApp():

    def __init__(self):
        super().__init__()
        CoroutineScheduler.start_interval_jobs()
