from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine


class Migration:

    def __init__(self, url=None,
                       dialect=None, driver=None, username=None, password=None, host=None, port=None, database=None):
        if not url:
            url = f'{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}'
        self.db_url = url
        self.alembic_cfg = self.create_alembic_config()

    def create_alembic_config(self):
        # https://alembic.sqlalchemy.org/en/latest/api/config.html
        alembic_cfg = Config()
        alembic_cfg.set_main_option('sqlalchemy.url', str(self.db_url).replace('%', '%%'))
        alembic_cfg.set_main_option('script_location', './lation/core/migration')
        alembic_cfg.set_main_option('version_locations', './lation/core/migration/versions')
        return alembic_cfg

    def revision(self):
        command.revision(self.alembic_cfg, message='Revision generated from lation command', autogenerate=True)

    def upgrade(self, revision='head'):
        command.upgrade(self.alembic_cfg, revision)

    def downgrade(self, revision='-1'):
        command.downgrade(self.alembic_cfg, revision)
