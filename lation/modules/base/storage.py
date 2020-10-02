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

class RemoteStorage(Storage):
    def serialize_name(self, name_list):
        return '/'.join(name_list)

    def deserialize_name(self, serialized_name):
        return serialized_name.split('/')

    def to_remote_mime(self, local_mime):
        raise NotImplementedError

    def to_local_mime(self, remote_mime):
        raise NotImplementedError

    def upload(self):
        raise NotImplementedError

    def download(self):
        raise NotImplementedError
