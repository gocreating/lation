import enum

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from lation.modules.base.storage import RemoteStorage

# https://developers.google.com/drive/api/v3/about-auth
SCOPES = [
    'https://www.googleapis.com/auth/drive',
]

class GoogleDriveUtility():
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

class GoogleDriveStorage(RemoteStorage):
    # https://developers.google.com/drive/api/v3/mime-types
    class MIMETypeEnum(enum.Enum):
        FOLDER = 'application/vnd.google-apps.folder'
        SPREAD_SHEET = 'application/vnd.google-apps.spreadsheet'
        UNKNOWN = 'application/vnd.google-apps.unknown'

    file_fields = ['id', 'name', 'mimeType', 'parents']

    def __init__(self, credential_path=None, **kwargs):
        if not credential_path:
            raise Exception('Credential path is required')
        super().__init__(**kwargs)
        credentials = Credentials.from_service_account_file(credential_path, scopes=SCOPES)
        self.service = build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def change_directory(self, serialized_name):
        self.current_working_folder_id = None
        if serialized_name:
            cwd = self.deserialize_name(serialized_name)
            current_working_folder = self._get_folder_by_names(cwd)
            if not current_working_folder:
                raise Exception('Base directory does not exist')
            self.current_working_folder_id = current_working_folder['id']

    def _list_all_items(self, query=None):
        page_token = None
        accumulated_files = []
        if query == None:
            query = {}
        query_str = GoogleDriveUtility.get_query_str(**query)
        file_fields = ','.join(GoogleDriveStorage.file_fields)
        while True:
            response = self.service.files().list(q=query_str,
                                                 fields=f'nextPageToken, files({file_fields})',
                                                 pageToken=page_token).execute()
            files = response.get('files', [])
            page_token = response.get('nextPageToken', None)
            accumulated_files.extend(files)
            if page_token is None:
                return accumulated_files

    def _create_folder(self, folder_name, parent_folder_id=None):
        file_metadata = {
            'name': folder_name,
            'mimeType': GoogleDriveStorage.MIMETypeEnum.FOLDER.value,
            'parents': parent_folder_id if isinstance(parent_folder_id, list) else [parent_folder_id],
        }
        file_fields = ','.join(GoogleDriveStorage.file_fields)
        folder = self.service.files().create(body=file_metadata,
                                             fields=file_fields).execute()
        return folder

    def _get_folder_by_name(self, folder_name, parent_folder_id=None, create_on_not_exist=False):
        folders = self._list_all_items({
            'name': folder_name,
            'parents': parent_folder_id,
            'mime_type': GoogleDriveStorage.MIMETypeEnum.FOLDER.value,
            'trashed': False,
        })
        if len(folders) == 0:
            if create_on_not_exist:
                folder = self._create_folder(folder_name, parent_folder_id)
                return folder
            else:
                raise Exception(f'Folder `{folder_name}` does not exist')
        elif len(folders) == 1:
            return folders[0]
        else:
            raise Exception(f'Detect duplicate folder `{folder_name}`')

    def _get_folder_by_names(self, folder_names, root_folder_id=None):
        parent_folder_id = root_folder_id
        for folder_name in folder_names:
            folder = self._get_folder_by_name(folder_name, parent_folder_id=parent_folder_id)
            parent_folder_id = folder['id']
        return folder

    def _delete_item(self, item_id):
        response = self.service.files().delete(fileId=item_id).execute()
        return response

    def list_directory(self, name=None, **kwargs):
        if not name:
            parent_folder_id = self.current_working_folder_id
        else:
            folder = self._get_folder_by_names(name, root_folder_id=self.current_working_folder_id)
            parent_folder_id = folder['id']
        items = self._list_all_items({
            'parents': parent_folder_id,
            'trashed': False,
        })
        return items

    def create_directory(self, name, **kwargs):
        parent_folder_id = self.current_working_folder_id
        for folder_name in name:
            folder = self._get_folder_by_name(folder_name, parent_folder_id=parent_folder_id, create_on_not_exist=True)
            parent_folder_id = folder['id']
        return folder

    def delete_directory(self, name, **kwargs):
        folder = self._get_folder_by_names(name, root_folder_id=self.current_working_folder_id)
        return self._delete_item(folder['id'])
