import ast
import csv
import json
import os

from sqlalchemy import create_engine, schema
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import JSON

from lation.core.importer import dynamic_import
from lation.file_manager import FileManager

class DatabaseManager():
    def __init__(self, host, username, password, database, port=3306):
        self.engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}')
        metadata = schema.MetaData()
        metadata.reflect(bind=self.engine)
        self.tables = metadata.sorted_tables
        self.Session = sessionmaker(bind=self.engine)

    def find_table(self, table_name):
        table = next((table for table in self.tables if table.name == table_name), None)
        return table

    def get_table_from_file_path(self, file_path):
        filename = os.path.basename(file_path)
        table_name = os.path.splitext(filename)[0]
        return self.find_table(table_name)

    def is_json_column(self, column):
        return isinstance(column.type, JSON)

    def export_csv_from_db(self, target_dir):
        dir_path = FileManager.prepare_dir(target_dir)
        for table in self.tables:
            file_path = os.path.join(dir_path, f'{table.name}.csv')
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                column_names = [column.name for column in table.columns]
                writer = csv.DictWriter(csv_file, fieldnames=column_names)
                writer.writeheader()
                rows = self.engine.execute(table.select())
                for row in rows:
                    row_dict = dict(row)
                    writer.writerow(row_dict)

    def import_csv_from_module(self, module_name):
        file_paths = dynamic_import(f'lation.modules.{module_name}.__lation__', 'data')
        session = self.Session()

        for table in reversed(self.tables):
            session.execute(table.delete())

        for file_path in file_paths:
            table = self.get_table_from_file_path(file_path)
            json_column_names = [column.name for column in table.columns if self.is_json_column(column)]
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
        session.commit()
