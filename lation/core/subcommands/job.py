import click

from lation.core.command import cli
from lation.modules.base.models.job import Scheduler, JobWorker

@cli.group('job')
def job_cmd_group():
    pass

"""
Usage:
    python lation.py job scheduler
"""
@job_cmd_group.command('scheduler')
def job_scheduler():
    Scheduler.run_forever()

"""
Usage:
    python lation.py job worker
"""
@job_cmd_group.command('worker')
def job_worker():
    JobWorker.run_forever()
