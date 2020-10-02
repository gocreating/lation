import click
import json

from lation.core.command import cli
from lation.modules.base.google_drive_storage import GoogleDriveStorage

@cli.group('google-drive')
@click.option('--credential-path')
@click.option('--cwd', default='lation')
@click.pass_context
def google_drive(ctx, credential_path, cwd):
    google_drive_storage = GoogleDriveStorage(credential_path=credential_path)
    google_drive_storage.change_directory(cwd)
    ctx.obj = google_drive_storage

"""
Usage:
    python lation.py google-drive --credential-path c list --name n
"""
@google_drive.command('list')
@click.pass_obj
@click.option('--name')
def google_drive_list(google_drive_storage, name):
    name = google_drive_storage.deserialize_name(name)
    results = google_drive_storage.list_directory(name)
    print(json.dumps(results, indent=4))

"""
Usage:
    python lation.py google-drive --credential-path c create-dir --name n
"""
@google_drive.command('create-dir')
@click.pass_obj
@click.option('--name')
def google_drive_create_dir(google_drive_storage, name):
    name = google_drive_storage.deserialize_name(name)
    results = google_drive_storage.create_directory(name)
    print(json.dumps(results, indent=4))

"""
Usage:
    python lation.py google-drive --credential-path c delete-dir --name n
"""
@google_drive.command('delete-dir')
@click.pass_obj
@click.option('--name')
def google_drive_delete_dir(google_drive_storage, name):
    name = google_drive_storage.deserialize_name(name)
    google_drive_storage.delete_directory(name)

"""
Usage:
    python lation.py google-drive --credential-path c upload-file --local l --remote r
"""
@google_drive.command('upload-file')
@click.pass_obj
@click.option('--local')
@click.option('--remote')
def google_drive_upload_file(google_drive_storage, local, remote):
    local_names = google_drive_storage.fs.deserialize_name(local)
    remote_names = google_drive_storage.deserialize_name(remote)
    google_drive_storage.upload_file(local_names, remote_names)

"""
Usage:
    python lation.py google-drive --credential-path c upload-dir --local l --remote r
"""
@google_drive.command('upload-dir')
@click.pass_obj
@click.option('--local')
@click.option('--remote')
def google_drive_upload_dir(google_drive_storage, local, remote):
    local_names = google_drive_storage.fs.deserialize_name(local)
    remote_names = google_drive_storage.deserialize_name(remote)
    google_drive_storage.upload_directory(local_names, remote_names)

"""
Usage:
    python lation.py google-drive --credential-path c download-file --local l --remote r
"""
@google_drive.command('download-file')
@click.pass_obj
@click.option('--local')
@click.option('--remote')
def google_drive_download_file(google_drive_storage, local, remote):
    local_names = google_drive_storage.fs.deserialize_name(local)
    remote_names = google_drive_storage.deserialize_name(remote)
    google_drive_storage.download_file(remote_names, local_names)

"""
Usage:
    python lation.py google-drive --credential-path c download-dir --local l --remote r
"""
@google_drive.command('download-dir')
@click.pass_obj
@click.option('--local')
@click.option('--remote')
def google_drive_download_dir(google_drive_storage, local, remote):
    local_names = google_drive_storage.fs.deserialize_name(local)
    remote_names = google_drive_storage.deserialize_name(remote)
    google_drive_storage.download_directory(remote_names, local_names)
