from flask import Flask, Response as FlaskResponse, jsonify

class CustomResponse(FlaskResponse):
    @classmethod
    def force_type(cls, response, environ=None):
        if isinstance(response, (list, dict)):
            response = jsonify(response)
        return super(FlaskResponse, cls).force_type(response, environ)

class BaseFlask(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.response_class = CustomResponse

        @self.route('/')
        def liveness():
            return {'status': 0}
