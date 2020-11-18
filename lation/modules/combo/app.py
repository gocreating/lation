from lation.modules.base_flask.base_flask import BaseFlask

class ComboFlaskApp(BaseFlask):
    def __init__(self):
        super().__init__()

        @self.route('/combo')
        def combo():
            return {
                'status': 0,
                'data': 'Welcome to combo api',
            }

app = ComboFlaskApp()
