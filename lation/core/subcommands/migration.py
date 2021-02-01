import click

from lation.core.command import Mutex, cli
from lation.core.migration.migration import Migration
from lation.core.env import get_env


APP = get_env('APP')

@cli.group('migration')
@click.pass_context
@click.option('--url', cls=Mutex, not_required_if=['dialect', 'driver', 'username', 'password', 'host', 'port', 'database'])
@click.option('--dialect', cls=Mutex, not_required_if=['url'])
@click.option('--driver', cls=Mutex, not_required_if=['url'])
@click.option('--username', cls=Mutex, not_required_if=['url'])
@click.option('--password', cls=Mutex, not_required_if=['url'])
@click.option('--host', cls=Mutex, not_required_if=['url'])
@click.option('--port', cls=Mutex, not_required_if=['url'])
@click.option('--database', cls=Mutex, not_required_if=['url'])
def migration(ctx, url, dialect, driver, username, password, host, port, database):
    migration = Migration(url=url,
                          dialect=dialect,
                          driver=driver,
                          username=username,
                          password=password,
                          host=host,
                          port=port,
                          database=database)
    ctx.obj = migration

"""
Usage:
    APP=combo python lation.py migration --url u revision
"""
@migration.command('revision')
@click.option('--force', is_flag=True, help='Set this option to force drop alembic version table and clear version location')
@click.pass_obj
def migration_revision(migration, force):
    if force:
        migration.force_revision()
    else:
        migration.revision()

"""
Usage:
    APP=combo python lation.py migration --url u upgrade
"""
@migration.command('upgrade')
@click.pass_obj
def migration_upgrade(migration):
    migration.upgrade()

"""
Usage:
    APP=combo python lation.py migration --url u downgrade
"""
@migration.command('downgrade')
@click.pass_obj
def migration_downgrade(migration):
    migration.downgrade()
