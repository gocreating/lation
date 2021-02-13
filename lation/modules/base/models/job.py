import functools
import time
from datetime import datetime

from croniter import croniter
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from lation.core.database.database import Database
from lation.core.database.types import STRING_L_SIZE, STRING_S_SIZE, STRING_XS_SIZE, Boolean, DateTime, Integer, String
from lation.core.env import get_env
from lation.core.orm import Base


DB_URL = get_env('DB_URL')


class CronJobLog(Base):
    __tablename__ = 'cron_job_log'

    cron_job_id = Column(Integer, ForeignKey('cron_job.id'), index=True)
    cron_job = relationship('CronJob', foreign_keys=[cron_job_id])

    execute_time = Column(DateTime)
    finish_time = Column(DateTime)
    exception = Column(String(STRING_L_SIZE))


class CronJob(Base):
    __tablename__ = 'cron_job'

    name = Column(String(STRING_S_SIZE), nullable=False)
    is_active = Column(Boolean, default=True)
    schedule = Column(String(STRING_XS_SIZE), nullable=False, comment='Cron expression. e.g. `0 */5 * * *`')

    latest_cron_job_log_id = Column(Integer, ForeignKey('cron_job_log.id'), index=True)
    latest_cron_job_log = relationship('CronJobLog', foreign_keys=[latest_cron_job_log_id])

    @property
    def should_execute(self):
        if not self.is_active:
            return False
        return croniter.match(self.schedule, datetime.utcnow())

    def execute(self):
        func = Scheduler.get_cron_job(self.name)
        if not func:
            raise Exception(f'Cron job `{self.name}` is not registered')
        func(self)


class Scheduler():

    fn_map = {}

    @staticmethod
    def register_cron_job():

        def decorator(func):
            Scheduler.fn_map[func.__name__] = func

            @functools.wraps(func)
            def wrapped_func(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapped_func

        return decorator

    @staticmethod
    def get_cron_job(fn_name):
        return Scheduler.fn_map.get(fn_name)

    @staticmethod
    def run():
        database = Database(url=DB_URL)

        while True:
            utc_now = datetime.utcnow()
            seconds_to_next_minute = 60 - utc_now.second
            time.sleep(seconds_to_next_minute)

            try:
                session = database.get_session()
                cron_jobs = session.query(CronJob).all()
            except Exception as e:
                print(e)
                cron_jobs = []

            for cron_job in cron_jobs:
                if cron_job.should_execute:
                    cron_job_log = CronJobLog(cron_job=cron_job)
                    session.add(cron_job_log)
                    session.flush()
                    try:
                        execute_time = datetime.utcnow()
                        cron_job.execute()
                    except Exception as e:
                        cron_job_log.exception = repr(e)
                    finally:
                        cron_job_log.execute_time = execute_time
                        cron_job_log.finish_time = datetime.utcnow()
                        cron_job.latest_cron_job_log_id = cron_job_log.id
                        session.commit()
