import asyncio
import click

from lation.core.command import cli
from lation.modules.base.models.job import CoroutineScheduler, Scheduler, JobWorker

@cli.group('job')
def job_cmd_group():
    pass

"""
Usage:
    python lation.py job scheduler
"""
@job_cmd_group.command('scheduler')
def job_scheduler():
    # https://www.technugget.net/using-pythons-asyncio-asynchronously-run-existing-blocking-code-2020/
    async def run_schedulers_concurrently():
        loop = asyncio.get_running_loop()
        result = await asyncio.gather(
            CoroutineScheduler.start_interval_jobs(),
            await loop.run_in_executor(None, lambda: Scheduler.run_forever())
        )
    asyncio.run(run_schedulers_concurrently())

"""
Usage:
    python lation.py job worker
"""
@job_cmd_group.command('worker')
def job_worker():
    JobWorker.run_forever()
