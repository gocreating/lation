import enum
import os

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from lation.file_manager import FileManager

# https://developers.google.com/drive/api/v3/about-auth
SCOPES = [
    'https://www.googleapis.com/auth/drive',
]

class GoogleDriveManager():
    # https://developers.google.com/drive/api/v3/mime-types
    class RemoteMIMETypeEnum(enum.Enum):
        DRIVE_SPREAD_SHEET = 'application/vnd.google-apps.spreadsheet'
        DRIVE_FOLDER = 'application/vnd.google-apps.folder'
        DRIVE_UNKNOWN = 'application/vnd.google-apps.unknown'

    class LocalMIMETypeEnum(enum.Enum):
        CSV = 'text/csv'

    # https://developers.google.com/drive/api/v3/manage-uploads
    @staticmethod
    def get_compatible_remote_mime_type(local_mime_type):
        if local_mime_type == GoogleDriveManager.LocalMIMETypeEnum.CSV.value:
            return GoogleDriveManager.RemoteMIMETypeEnum.DRIVE_SPREAD_SHEET.value
        return GoogleDriveManager.RemoteMIMETypeEnum.DRIVE_UNKNOWN.value

    @staticmethod
    def get_query_str(name=None, mime_type=None, trashed=None, parents=None):
        queries = []
        if name != None:
            queries.append(f"name = '{name}'")
        if mime_type != None:
            queries.append(f"mimeType = '{mime_type}'")
        if trashed != None:
            if trashed == True:
                queries.append('trashed = true')
            elif trashed == False:
                queries.append('trashed = false')
        if parents != None:
            if isinstance(object, list):
                queries.append(f"'{parents[0]}' in parents")
            else:
                queries.append(f"'{parents}' in parents")
        return ' and '.join(queries)

    def __init__(self, credential_path, base_folder_names=None):
        credentials = Credentials.from_service_account_file(credential_path, scopes=SCOPES)
        self.service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
        self.base_folder_names = base_folder_names

    # retrieve all paged files and folders from given query
    def list_all(self, query=None):
        page_token = None
        accumulated_files = []
        if query == None:
            query = {}
        query_str = GoogleDriveManager.get_query_str(**query)
        while True:
            response = self.service.files().list(q=query_str,
                                                 fields="nextPageToken, files(id, name, parents)",
                                                 pageToken=page_token).execute()
            files = response.get('files', [])
            page_token = response.get('nextPageToken', None)
            accumulated_files.extend(files)
            if page_token is None:
                return accumulated_files

    def find_folders_by_name(self, folder_name, parent_folder=None):
        folders = self.list_all({
            'name': folder_name,
            'parents': parent_folder,
            'mime_type': GoogleDriveManager.RemoteMIMETypeEnum.DRIVE_FOLDER.value,
            'trashed': False,
        })
        return folders

    def create_folder(self, folder_name, parent_folder=None):
        file_metadata = {
            'name': folder_name,
            'mimeType': GoogleDriveManager.RemoteMIMETypeEnum.DRIVE_FOLDER.value,
            'parents': parent_folder if isinstance(object, list) else [parent_folder],
        }
        folder = self.service.files().create(body=file_metadata,
                                             fields='id,parents').execute()
        return folder

    def get_folder_by_name(self, folder_name, parent_folder=None):
        folders = self.find_folders_by_name(folder_name, parent_folder)
        if len(folders) == 0:
            raise Exception(f'Folder `{folder_name}` does not exist')
        elif len(folders) == 1:
            return folders[0]
        else:
            raise Exception(f'Detect duplicate folder `{folder_name}`')

    def get_deep_folder(self, folder_names):
        parent_folder = None
        for folder_name in folder_names:
            folder = self.get_folder_by_name(folder_name, parent_folder=parent_folder)
            parent_folder = folder['id']
        return folder

    def create_or_get_folder(self, folder_name, parent_folder=None):
        folders = self.find_folders_by_name(folder_name, parent_folder)
        if len(folders) == 0:
            folder = self.create_folder(folder_name, parent_folder)
            return folder
        elif len(folders) == 1:
            return folders[0]
        else:
            raise Exception(f'Detect duplicate folder `{folder_name}`')

    def create_or_get_deep_folder(self, folder_names):
        parent_folder = None
        for folder_name in folder_names:
            folder = self.create_or_get_folder(folder_name, parent_folder=parent_folder)
            parent_folder = folder['id']
        return folder

    def upload_dir(self, local_dir, remote_folders):
        folder = self.create_or_get_deep_folder(remote_folders)
        _, local_dir_names, local_file_names = next(walk(local_dir))

        for local_file_name in local_file_names:
            local_file_path = os.path.join(local_dir, local_file_name)
            mime_type = FileManager.get_mime_type(local_file_path)
            file_metadata = {
                'name': local_file_name,
                'mimeType': GoogleDriveManager.get_compatible_remote_mime_type(mime_type),
                'parents': [folder['id']],
            }
            media = MediaFileUpload('exported-data/Session.csv', mimetype=mime_type)
            self.service.files().create(body=file_metadata,
                                        media_body=media,
                                        fields='id').execute()

    def delete_by_id(self, file_id):
        self.service.files().delete(fileId=file_id).execute()

    def delete_deep_folder(self, folder_names):
        folder = self.get_deep_folder(folder_names)
        self.delete_by_id(folder['id'])
