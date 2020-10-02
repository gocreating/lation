import mimetypes
import os

from lation.modules.base.storage import LocalStorage

class FileSystem(LocalStorage):
    def __init__(self, **kwargs):
        self.cwd = os.getcwd()

    def get_mime_type(self, name, **kwargs):
        target_path = os.path.join(self.cwd, *name)
        mime_type = mimetypes.guess_type(target_path)[0]
        return mime_type

    def is_file(self, name, **kwargs):
        target_path = os.path.join(self.cwd, *name)
        return os.path.isfile(target_path)

    def is_directory(self, name, **kwargs):
        target_path = os.path.join(self.cwd, *name)
        return os.path.isdir(target_path)

    def change_directory(self, serialized_name):
        cwd = os.path.join(os.getcwd(), *self.deserialize_name(serialized_name))
        self.cwd = cwd

    def list_directory(self, name=None, **kwargs):
        target_path = os.path.join(self.cwd, *name)
        return os.listdir(target_path)

    def create_directory(self, name, **kwargs):
        target_path = os.path.join(self.cwd, *name)
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        return target_path
