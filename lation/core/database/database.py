import ast
import csv
import functools
import os
import time

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.schema import CreateSchema, DropSchema, MetaData
from sqlalchemy.types import JSON

from lation.core.env import get_env
from lation.core.logger import create_logger
from lation.core.module import modules
from lation.modules.base.file_system import FileSystem


APP = get_env('APP')

class Database():

    @staticmethod
    def get_metadata():
        return MetaData(schema=APP)

    def __init__(self, url=None,
                       dialect=None, driver=None, username=None, password=None, host=None, port=None, database=None,
                       model_agnostic=False):
        from lation.core.orm import Base

        if not url:
            url = f'{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}'
        self.engine = create_engine(url, pool_size=1)
        SessionFactory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        self.Session = scoped_session(SessionFactory)
        self.model_agnostic = model_agnostic
        existing_metadata = Database.get_metadata()
        existing_metadata.reflect(bind=self.engine, schema=APP)
        self.existing_metadata = existing_metadata
        self.metadata = Base.metadata
        self.fs = FileSystem()
        self.logger = create_logger()
        self.Base = Base

    def get_session(self):
        try:
            session = self.Session()
            return session
        finally:
            session.close()

    @functools.lru_cache()
    def find_tablename_by_file_path(self, file_path):
        filename = os.path.basename(file_path)
        table_name = os.path.splitext(filename)[0]
        return table_name

    # def find_table_by_file_path(self, file_path):
    #     table_name = self.find_tablename_by_file_path(file_path)
    #     return self.metadata.tables[f'{APP}.{table_name}']

    @functools.lru_cache()
    def find_model_class_by_tablename(self, tablename):
        for model_class in self.Base._decl_class_registry.values():
            if hasattr(model_class, '__tablename__') and model_class.__tablename__ == tablename:
                return model_class
        return None

    def is_json_column(self, column):
        return isinstance(column.type, JSON)

    def is_json_attribute(self, attribute):
        return isinstance(attribute.columns[0].type, JSON)

    def export(self, dir_path):
        self.fs.create_directory(self.fs.deserialize_name(dir_path))
        for table in self.metadata.sorted_tables:
            self.logger.info(f'EXPORT TABLE `{table.name}`...')
            file_path = os.path.join(dir_path, f'{table.name}.csv')
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                column_names = [column.name for column in table.columns]
                writer = csv.DictWriter(csv_file, fieldnames=column_names)
                writer.writeheader()
                rows = self.engine.execute(table.select())
                for row in rows:
                    row_dict = dict(row)
                    writer.writerow(row_dict)
            self.logger.info(f'EXPORT TABLE `{table.name}` DONE')

    def drop_schema(self, schema_name):
        self.engine.execute(DropSchema(schema_name))
        self.logger.info(f'DELETE SCHEMA `{schema_name}`')

    def create_schema(self, schema_name):
        self.engine.execute(CreateSchema(schema_name))
        self.logger.info(f'CREATE SCHEMA `{schema_name}`')

    def drop_tables(self):
        self.existing_metadata.drop_all(self.engine)
        self.logger.info('DELETE ALL TABLES')

    # drop tables one by one
    def destruct_tables(self):
        for table in reversed(self.metadata.sorted_tables):
            session.execute(table.delete())

    def create_tables(self):
        self.metadata.create_all(self.engine)
        self.logger.info(f'ALL TABLES CREATED')

    def dispose(self):
        self.engine.dispose()

    def install_data(self, module_name):
        for parent_module in modules[module_name].parent_modules:
            self.install_data(parent_module.name)
        start_time = time.process_time()
        partial_csv_file_paths = modules[module_name].config.data
        if len(partial_csv_file_paths) == 0:
            self.logger.info(f'[{module_name}] NO DATA, SKIPPED')
            return
        self.logger.info(f'[{module_name}] INSTALL DATA...')
        session = self.get_session()

        for partial_csv_file_path in partial_csv_file_paths:
            csv_file_path = os.path.join('lation', 'modules', module_name, partial_csv_file_path)
            tablename = self.find_tablename_by_file_path(csv_file_path)
            model_class = self.find_model_class_by_tablename(tablename)
            inspector = inspect(model_class)
            json_type_attribute_names = [attr.key for attr in inspector.mapper.column_attrs if self.is_json_attribute(attr)]
            self.logger.info(f'[{module_name}] INTO TABLE `{tablename}` FROM PATH `{csv_file_path}`')

            with open(csv_file_path, newline='', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for csv_data in reader:
                    # load data
                    if csv_data == '':
                        continue
                    attribute_data = {}
                    for attribute_name in csv_data.keys():
                        csv_value = csv_data[attribute_name]
                        if csv_value == '':
                            continue
                        if attribute_name in json_type_attribute_names:
                            attribute_data[attribute_name] = ast.literal_eval(csv_value)
                        else:
                            attribute_data[attribute_name] = csv_value

                    # validate lation_id
                    lation_id = attribute_data.get('lation_id')
                    if not lation_id:
                        raise Exception(f'Attribute `lation_id` is required for csv file `{csv_file_path}`')
                    lation_id_parts = lation_id.split('.')
                    if len(lation_id_parts) < 2 or lation_id_parts[0] != module_name:
                        lation_id = f'{module_name}.{lation_id}'
                        attribute_data['lation_id'] = lation_id

                    # upsert instance
                    instance = session.query(model_class).filter(model_class.lation_id == lation_id).one_or_none()
                    if instance:
                        for attribute_name in attribute_data:
                            setattr(instance, attribute_name, attribute_data[attribute_name])
                    else:
                        instance = model_class(**attribute_data)
                        session.add(instance)

            # Fix postgres sequence, see <https://stackoverflow.com/a/37972960/2443984>
            if session.bind.dialect.name == 'postgresql':
                for table in inspector.tables:
                    session.execute(f'SELECT setval(pg_get_serial_sequence(\'{table.fullname}\', \'id\'), coalesce(max(id)+1, 1), false) FROM {table.fullname};')

            session.flush()
            self.logger.info(f'[{module_name}] FLUSHED')

        self.logger.info(f'[{module_name}] COMMIT...')
        session.commit()
        self.logger.info(f'[{module_name}] COMMITTED')
        self.logger.info(f'[{module_name}] INSTALL DATA DONE IN {time.process_time() - start_time}s')

    def reset(self):
        if self.engine.dialect.has_schema(self.engine, schema=APP):
            self.drop_tables()
            self.drop_schema(APP)
        self.create_schema(APP)
        self.create_tables()
        self.install_data(APP)
