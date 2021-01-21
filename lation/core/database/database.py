import ast
import csv
import os

from sqlalchemy import create_engine, schema
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema
from sqlalchemy.types import JSON

from lation.core.env import get_env
from lation.core.logger import create_logger
from lation.core.module import modules
from lation.core.orm import Base
from lation.modules.base.file_system import FileSystem

APP = get_env('APP')

class Database():
    def __init__(self, url=None,
                       dialect=None, driver=None, username=None, password=None, host=None, port=None, database=None,
                       model_agnostic=False):
        if not url:
            url = f'{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}'
        self.engine = create_engine(url, pool_size=1)
        SessionFactory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(SessionFactory)
        self.model_agnostic = model_agnostic
        existing_metadata = schema.MetaData()
        existing_metadata.reflect(bind=self.engine, schema=APP)
        self.existing_metadata = existing_metadata
        self.metadata = Base.metadata
        self.fs = FileSystem()
        self.logger = create_logger()

    def get_session(self):
        try:
            session = self.Session()
            return session
        finally:
            session.close()

    def get_table_from_file_path(self, file_path):
        filename = os.path.basename(file_path)
        table_name = os.path.splitext(filename)[0]
        return self.metadata.tables[f'{APP}.{table_name}']

    def is_json_column(self, column):
        return isinstance(column.type, JSON)

    def export(self, dir_path):
        self.fs.create_directory(self.fs.deserialize_name(dir_path))
        for table in self.metadata.sorted_tables:
            self.logger.info(f'EXPORT TABLE {table.name}...')
            file_path = os.path.join(dir_path, f'{table.name}.csv')
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                column_names = [column.name for column in table.columns]
                writer = csv.DictWriter(csv_file, fieldnames=column_names)
                writer.writeheader()
                rows = self.engine.execute(table.select())
                for row in rows:
                    row_dict = dict(row)
                    writer.writerow(row_dict)
            self.logger.info(f'EXPORT TABLE {table.name} DONE')

    def drop_schema(self, schema_name):
        self.engine.execute(DropSchema(schema_name))

    def create_schema(self, schema_name):
        self.engine.execute(CreateSchema(schema_name))

    def drop_tables(self):
        self.existing_metadata.drop_all(self.engine)

    def create_tables(self):
        self.metadata.create_all(self.engine)

    def dispose(self):
        self.engine.dispose()

    def install_data(self, module_name):
        for parent_module in modules[module_name].parent_modules:
            self.install_data(parent_module.name)
        file_paths = modules[module_name].config.data
        session = self.get_session()
        for file_path in file_paths:
            table = self.get_table_from_file_path(file_path)
            json_column_names = [column.name for column in table.columns if self.is_json_column(column)]
            self.logger.info(f'IMPORT TABLE {table.name}...')
            with open(file_path, newline='', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for raw_row in reader:
                    row = {}
                    for col in raw_row.keys():
                        raw_value = raw_row[col]
                        if raw_value != '':
                            if col in json_column_names:
                                row[col] = ast.literal_eval(raw_value)
                            else:
                                row[col] = raw_value
                    session.execute(table.insert(row))

            # Fix postgres sequence, see <https://stackoverflow.com/a/37972960/2443984>
            if session.bind.dialect.name == 'postgresql':
                session.execute(f'SELECT setval(pg_get_serial_sequence(\'{table.fullname}\', \'id\'), coalesce(max(id)+1, 1), false) FROM {table.fullname};')

            session.flush()
            self.logger.info(f'IMPORT TABLE {table.name} FLUSHED')

        self.logger.info(f'IMPORT TABLES COMMIT...')
        session.commit()
        self.logger.info(f'IMPORT TABLES COMMITTED')

    def reset(self):
        if self.engine.dialect.has_schema(self.engine, schema=APP):
            self.drop_tables()
            self.drop_schema(APP)
        self.create_schema(APP)
        self.create_tables()
        self.install_data(APP)
