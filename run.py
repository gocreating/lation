from gevent import monkey
from gevent.pywsgi import WSGIServer

from lation.core.module import dynamic_import, load_modules

monkey.patch_all()

servable_module_name = 'base_flask'

if __name__ == '__main__':
    module = load_modules()
    if module.name == servable_module_name or servable_module_name in [m.name for m in module.parent_modules]:
        module_app = dynamic_import(f'{module.module_path}.app')
        http_server = WSGIServer(('0.0.0.0', 8000), module_app.app)
        http_server.serve_forever()
    else:
        module.start_app()
