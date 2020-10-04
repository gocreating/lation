import click

from lation.core.command import Mutex, cli
from lation.core.database import Database
from lation.core.env import get_env

APP = get_env('APP')

@cli.group('db')
@click.pass_context
@click.option('--url', cls=Mutex, not_required_if=['dialect', 'driver', 'username', 'password', 'host', 'port', 'database'])
@click.option('--dialect', cls=Mutex, not_required_if=['url'])
@click.option('--driver', cls=Mutex, not_required_if=['url'])
@click.option('--username', cls=Mutex, not_required_if=['url'])
@click.option('--password', cls=Mutex, not_required_if=['url'])
@click.option('--host', cls=Mutex, not_required_if=['url'])
@click.option('--port', cls=Mutex, not_required_if=['url'])
@click.option('--database', 'database_name', cls=Mutex, not_required_if=['url'])
@click.option('--model-agnostic', is_flag=True, help='Set this option to reflect models from existing tables')
def db(ctx, url, dialect, driver, username, password, host, port, database_name, model_agnostic):
    database = Database(url=url,
                        dialect=dialect,
                        driver=driver,
                        username=username,
                        password=password,
                        host=host,
                        port=port,
                        database=database_name,
                        model_agnostic=model_agnostic)
    ctx.obj = database

"""
Usage:
    APP=combo python lation.py db --url u export
"""
@db.command('export')
@click.pass_obj
@click.option('--dest-dir', default='./exported-data')
def db_export(database, dest_dir):
    database.export(dest_dir)

"""
Usage:
    APP=combo python lation.py db --url u reset
"""
@db.command('reset')
@click.pass_obj
def db_reset(database):
    database.reset()
