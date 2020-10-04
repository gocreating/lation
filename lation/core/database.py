import ast
import csv
import os

from sqlalchemy import create_engine, schema
from sqlalchemy.orm import sessionmaker
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
        self.engine = create_engine(url)
        self.Session = sessionmaker(bind=self.engine)
        self.model_agnostic = model_agnostic
        if model_agnostic:
            metadata = schema.MetaData()
            metadata.reflect(bind=self.engine)
            self.metadata = metadata
        else:
            self.metadata = Base.metadata
        self.fs = FileSystem()
        self.logger = create_logger()

    def get_table_from_file_path(self, file_path):
        filename = os.path.basename(file_path)
        table_name = os.path.splitext(filename)[0]
        return self.metadata.tables[table_name]

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

    def reset(self):
        file_paths = modules[APP].config.data
        session = self.Session()
        if self.model_agnostic:
            for table in reversed(self.metadata.sorted_tables):
                session.execute(table.delete())
                self.logger.info(f'DELETE TABLE {table.name}')
            self.logger.info(f'DELETE TABLES FLUSHED')
        else:
            self.metadata.drop_all(self.engine)
            self.logger.info(f'DROP TABLES DONE')
            self.metadata.create_all(self.engine)
            self.logger.info(f'CREATE TABLES DONE')

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
            session.flush()
            self.logger.info(f'IMPORT TABLE {table.name} FLUSHED')

        self.logger.info(f'IMPORT TABLES COMMIT...')
        session.commit()
        self.logger.info(f'IMPORT TABLES COMMITTED')
