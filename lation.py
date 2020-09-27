import click

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

if __name__ == '__main__':
    cli()
