import uvicorn

from gevent import monkey
from gevent.pywsgi import WSGIServer

from lation.core.module import dynamic_import, load_modules

monkey.patch_all()

wsgi_module_names = ['base_flask']
asgi_module_names = ['base_fastapi']

if __name__ == '__main__':
    module = load_modules()
    parent_module_names = [m.name for m in module.parent_modules]
    if module.name in wsgi_module_names or any([wsgi_module_name in parent_module_names for wsgi_module_name in wsgi_module_names]):
        module_app = dynamic_import(f'{module.module_path}.app')
        http_server = WSGIServer(('0.0.0.0', 8000), module_app.app)
        http_server.serve_forever()
    elif module.name in asgi_module_names or any([asgi_module_name in parent_module_names for asgi_module_name in asgi_module_names]):
        module_app = dynamic_import(f'{module.module_path}.app')
        uvicorn.run(module_app.app, host='0.0.0.0', port=8000, log_level='info', loop='none')
    else:
        module.start_app()
