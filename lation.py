import click

from lation.database_manager import DatabaseManager
from lation.file_manager import FileManager

@click.group()
def cli():
    pass

"""
Usage:
    python lation.py encrypt --src s --dest d --password p
"""
@cli.command('encrypt')
@click.option('--src')
@click.option('--dest')
@click.option('--password', prompt=True)
def encrypt(src, dest, password):
    file_manager = FileManager(source_path=src, destination_path=dest)
    file_manager.encrypt(password)

"""
Usage:
    python lation.py decrypt --src s --dest d --password p
"""
@cli.command('decrypt')
@click.option('--src')
@click.option('--dest')
@click.option('--password', prompt=True)
def decrypt(src, dest, password):
    file_manager = FileManager(source_path=src, destination_path=dest)
    file_manager.decrypt(password)

"""
Usage:
    python lation.py export-data --host h --username u --password p --database d
"""
@cli.command('export-data')
@click.option('--host')
@click.option('--username')
@click.option('--password')
@click.option('--database')
@click.option('--dest-dir', default='./exported-data')
def export_data(host, username, password, database, dest_dir):
    database_manager = DatabaseManager(host, username, password, database)
    database_manager.export_csv_from_db(dest_dir)

"""
Usage:
    python lation.py import-data --host h --username u --password p --database d
"""
@cli.command('import-data')
@click.option('--host')
@click.option('--username')
@click.option('--password')
@click.option('--database')
@click.option('--module-name')
def import_data(host, username, password, database, module_name):
    database_manager = DatabaseManager(host, username, password, database)
    database_manager.import_csv_from_module(module_name)

if __name__ == '__main__':
    cli()
