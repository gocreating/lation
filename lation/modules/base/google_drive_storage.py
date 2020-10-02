import enum
import io

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from lation.modules.base.file_system import FileSystem
from lation.modules.base.storage import Storage, RemoteStorage

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
        DOCUMENT = 'application/vnd.google-apps.document' # Google Docs
        DRAWING = 'application/vnd.google-apps.drawing' # Google Drawing
        FILE = 'application/vnd.google-apps.file' # Google Drive file
        FOLDER = 'application/vnd.google-apps.folder' # Google Drive folder
        PRESENTATION= 'application/vnd.google-apps.presentation' # Google Slides
        SPREAD_SHEET = 'application/vnd.google-apps.spreadsheet' # Google Sheets
        UNKNOWN = 'application/vnd.google-apps.unknown'

    file_fields = ['id', 'name', 'mimeType', 'parents']

    @staticmethod
    def is_google_doc_format(mime_type):
        return mime_type in [
            GoogleDriveStorage.MIMETypeEnum.DOCUMENT.value,
            GoogleDriveStorage.MIMETypeEnum.SPREAD_SHEET.value,
            GoogleDriveStorage.MIMETypeEnum.DRAWING.value,
            GoogleDriveStorage.MIMETypeEnum.PRESENTATION.value
        ]

    def __init__(self, credential_path=None, **kwargs):
        if not credential_path:
            raise Exception('Credential path is required')
        super().__init__(**kwargs)
        credentials = Credentials.from_service_account_file(credential_path, scopes=SCOPES)
        self.service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
        self.current_working_folder_id = None
        self.fs = FileSystem()

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

    def _get_folder_by_names(self, folder_names, root_folder_id=None, create_on_not_exist=False):
        parent_folder_id = root_folder_id
        for folder_name in folder_names:
            folder = self._get_folder_by_name(folder_name, parent_folder_id=parent_folder_id, create_on_not_exist=create_on_not_exist)
            parent_folder_id = folder['id']
        return folder

    def _delete_item(self, item_id):
        response = self.service.files().delete(fileId=item_id).execute()
        return response

    def change_directory(self, serialized_name):
        self.current_working_folder_id = None
        if serialized_name:
            cwd = self.deserialize_name(serialized_name)
            current_working_folder = self._get_folder_by_names(cwd)
            if not current_working_folder:
                raise Exception('Base directory does not exist')
            self.current_working_folder_id = current_working_folder['id']

    def to_remote_mime_type(self, local_mime_type):
        return local_mime_type

    # https://developers.google.com/drive/api/v3/ref-export-formats
    def to_local_mime_type(self, remote_mime_type):
        if remote_mime_type == GoogleDriveStorage.MIMETypeEnum.DOCUMENT.value:
            return Storage.MIMETypeEnum.TEXT.value
        elif remote_mime_type == GoogleDriveStorage.MIMETypeEnum.SPREAD_SHEET.value:
            return Storage.MIMETypeEnum.CSV.value
        else:
            raise Exception(f'Incompatible mime type: {remote_mime_type}')

    def to_local_extension(self, remote_mime_type):
        if remote_mime_type == GoogleDriveStorage.MIMETypeEnum.DOCUMENT.value:
            return 'txt'
        elif remote_mime_type == GoogleDriveStorage.MIMETypeEnum.SPREAD_SHEET.value:
            return 'csv'
        else:
            return None

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

    def _upload_file(self, local_names, remote_folder_id):
        local_mime_type = self.fs.get_mime_type(local_names)
        remote_mime_type = self.to_remote_mime_type(local_mime_type)
        file_metadata = {
            'name': local_names[-1],
            'mimeType': remote_mime_type,
            'parents': [remote_folder_id],
        }
        media = MediaFileUpload(self.fs.serialize_name(local_names), mimetype=local_mime_type)
        file_fields = ','.join(GoogleDriveStorage.file_fields)
        uploaded_file = self.service.files().create(body=file_metadata,
                                                    media_body=media,
                                                    fields=file_fields).execute()
        return uploaded_file

    def upload_file(self, local_names, remote_names, **kwargs):
        folder = self._get_folder_by_names(remote_names, root_folder_id=self.current_working_folder_id, create_on_not_exist=True)
        self._upload_file(local_names, folder['id'])

    def upload_directory(self, local_names, remote_names, **kwargs):
        folder = self._get_folder_by_names(remote_names, root_folder_id=self.current_working_folder_id, create_on_not_exist=True)
        local_dir = self.fs.serialize_name(local_names)
        items = self.fs.list_directory(local_names)
        for item in items:
            local_items = [*local_names, item]
            if self.fs.is_file(local_items):
                self._upload_file(local_items, folder['id'])
            elif self.fs.is_directory(local_items):
                self.upload_directory(local_items, [*remote_names, item])

    def _download_file(self, remote_file, local_names):
        remote_mime_type = remote_file['mimeType']
        file_id = remote_file['id']
        if GoogleDriveStorage.is_google_doc_format(remote_mime_type):
            local_mime_type = self.to_local_mime_type(remote_mime_type)
            local_extension = self.to_local_extension(remote_mime_type)
            if local_extension:
                local_names[-1] = f'{local_names[-1]}.{local_extension}'
            request = self.service.files().export_media(fileId=file_id,
                                                        mimeType=local_mime_type)
        else:
            request = self.service.files().get_media(fileId=file_id)

        fh = io.FileIO(self.fs.serialize_name(local_names), mode='wb')
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print("Download %d%%." % int(status.progress() * 100))

    def download_directory(self, remote_names, local_names, **kwargs):
        self.fs.create_directory(local_names)
        folder = self._get_folder_by_names(remote_names, root_folder_id=self.current_working_folder_id)
        items = self.list_directory(remote_names)
        for item in items:
            local_items = [*local_names, item['name']]
            if item['mimeType'] == GoogleDriveStorage.MIMETypeEnum.FOLDER.value:
                self.download_directory([*remote_names, item['name']], local_items)
            else:
                self._download_file(item, local_items)
