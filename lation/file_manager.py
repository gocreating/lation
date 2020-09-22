from ansible_vault import Vault

class FileManager():
    def __init__(self, source_path=None, destination_path=None):
        self.source_path = source_path
        self.destination_path = destination_path

    def encrypt(self, password):
        vault = Vault(password)
        if not self.source_path:
            raise Exception('Source file path is required')
        if not self.destination_path:
            raise Exception('Destination file path is required')
        with open(self.source_path) as input_file:
            raw_data = input_file.read()
        with open(self.destination_path, 'wb') as output_file:
            vault.dump(raw_data, output_file)

    def decrypt(self, password):
        vault = Vault(password)
        if not self.source_path:
            raise Exception('Source file path is required')
        if not self.destination_path:
            raise Exception('Destination file path is required')
        with open(self.source_path) as input_file:
            decrypted_data = vault.load(input_file.read())
        with open(self.destination_path, 'w') as output_file:
            output_file.write(decrypted_data)
