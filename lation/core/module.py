import importlib

from lation.core.env import get_env

modules = {}

def dynamic_import(module_name, attr_name=None):
    module = importlib.import_module(module_name)
    if not attr_name:
        return module
    attr = getattr(module, attr_name)
    return attr

def is_exist(module_name):
    return importlib.util.find_spec(module_name)

class LationModule():
    def __init__(self, module_name):
        self.name = module_name
        self.module_path = f'lation.modules.{self.name}'
        if not is_exist(self.module_path):
            raise Exception(f'Module `{self.name}` not found')
        self.config = dynamic_import(f'{self.module_path}.__lation__')
        self.parent_modules = [LationModule(parent_module_name) for parent_module_name in self.config.parent_modules]

    def load(self):
        if self.name in modules:
            return
        for lation_module in self.parent_modules:
            lation_module.load()
        if is_exist(f'{self.module_path}.models'):
            self.models = dynamic_import(f'{self.module_path}.models')
        modules[self.name] = self

    def start_app(self):
        if is_exist(f'{self.module_path}.app'):
            dynamic_import(f'{self.module_path}.app')

def load_modules():
    APP = get_env('APP')
    if APP is None:
        raise Exception('Environment variable `APP` is required')
    module = LationModule(APP)
    module.load()
    return module
