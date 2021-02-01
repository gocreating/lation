import os
import shutil

from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData, create_engine
from sqlalchemy.schema import CreateSchema

from lation.core.env import get_env


APP = get_env('APP')

class Migration:

    def __init__(self, url=None,
                       dialect=None, driver=None, username=None, password=None, host=None, port=None, database=None):
        if not url:
            url = f'{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}'
        self.db_url = url
        self.alembic_cfg = self.create_alembic_config()

    def get_version_location(self):
        return './lation/core/migration/versions'

    def create_alembic_config(self):
        # https://alembic.sqlalchemy.org/en/latest/api/config.html
        alembic_cfg = Config()
        alembic_cfg.set_main_option('sqlalchemy.url', str(self.db_url).replace('%', '%%'))
        alembic_cfg.set_main_option('script_location', './lation/core/migration')
        version_location = self.get_version_location()
        if not os.path.exists(version_location):
            os.makedirs(version_location)
        alembic_cfg.set_main_option('version_locations', version_location)
        return alembic_cfg

    def revision(self):
        command.revision(self.alembic_cfg, message='Revision generated from lation command', autogenerate=True)

    def upgrade(self, revision='head'):
        command.upgrade(self.alembic_cfg, revision)

    def downgrade(self, revision='-1'):
        command.downgrade(self.alembic_cfg, revision)

    def force_revision(self):
        schema_name = APP
        engine = create_engine(self.db_url, pool_size=1)
        metadata = MetaData(schema=schema_name)
        metadata.reflect(bind=engine)
        alembic_version_table = metadata.tables.get(f'{schema_name}.alembic_version')
        if not engine.dialect.has_schema(engine, schema=schema_name):
            engine.execute(CreateSchema(schema_name))
        if alembic_version_table is not None:
            metadata.drop_all(engine, [alembic_version_table], checkfirst=True)
        version_location = self.get_version_location()
        shutil.rmtree(version_location, ignore_errors=True)
        self.revision()
