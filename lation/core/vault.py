from ansible.parsing.vault import AnsibleVaultError
from ansible_vault import Vault as AnsibleVault

from lation.modules.base.file_system import FileSystem

class Vault():
    @staticmethod
    def to_encrypted_name(name):
        return f'{name}.encrypted'

    @staticmethod
    def to_decrypted_name(name):
        return '.'.join(name.split('.')[:-1])

    def __init__(self, password):
        self.ansible_vault = AnsibleVault(password)
        self.fs = FileSystem()

    def encrypt(self, src, dest=None):
        srcs = self.fs.deserialize_name(src)
        assert self.fs.is_file(srcs), 'src should be a file'
        if not dest:
            dests = srcs.copy()
            dests[-1] = Vault.to_encrypted_name(srcs[-1])
            dest = self.fs.serialize_name(dests)
        with open(src, 'r') as input_file:
            raw_data = input_file.read()
        with open(dest, 'wb') as output_file:
            self.ansible_vault.dump(raw_data, output_file)

    def decrypt(self, src, dest=None):
        srcs = self.fs.deserialize_name(src)
        assert self.fs.is_file(srcs), 'src should be a file'
        if not dest:
            dests = srcs.copy()
            dests[-1] = Vault.to_decrypted_name(srcs[-1])
            dest = self.fs.serialize_name(dests)
        with open(src, 'r') as input_file:
            encrypted_data = input_file.read()
            try:
                decrypted_data = self.ansible_vault.load(encrypted_data)
            except AnsibleVaultError as e:
                raise Exception('Decrypt failed')
        with open(dest, 'w') as output_file:
            output_file.write(decrypted_data)
