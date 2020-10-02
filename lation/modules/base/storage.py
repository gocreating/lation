import enum

class Storage():
    class MIMETypeEnum(enum.Enum):
        TEXT = 'text/plain'
        CSV = 'text/csv'

    def serialize_name(self, name_list):
        raise NotImplementedError

    def deserialize_name(self, serialized_name):
        raise NotImplementedError

    def change_directory(self, serialized_name):
        raise NotImplementedError

    def is_file(self, name, **kwargs):
        raise NotImplementedError

    def is_directory(self, name, **kwargs):
        raise NotImplementedError

    """
    List all files and directories in a directory
    """
    def list_directory(self, name=None, **kwargs):
        raise NotImplementedError

    def create_directory(self, name, **kwargs):
        raise NotImplementedError

    def create_file(self, name, **kwargs):
        raise NotImplementedError

    def delete_directory(self, name, **kwargs):
        raise NotImplementedError

    def delete_file(self, name, **kwargs):
        raise NotImplementedError

class LocalStorage(Storage):
    def serialize_name(self, name_list):
        return '/'.join(name_list)

    def deserialize_name(self, serialized_name):
        return serialized_name.split('/')

    def get_mime_type(self, name, **kwargs):
        pass

class RemoteStorage(Storage):
    def serialize_name(self, name_list):
        return '/'.join(name_list)

    def deserialize_name(self, serialized_name):
        return serialized_name.split('/')

    def to_remote_mime_type(self, local_mime_type):
        raise NotImplementedError

    def to_local_mime_type(self, remote_mime_type):
        raise NotImplementedError

    def upload_file(self, local_names, remote_names, **kwargs):
        raise NotImplementedError

    def upload_directory(self, local_names, remote_names, **kwargs):
        raise NotImplementedError

    def download_file(self, remote_names, local_names, **kwargs):
        raise NotImplementedError

    def download_directory(self, remote_names, local_names, **kwargs):
        raise NotImplementedError
