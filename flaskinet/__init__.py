from flask import Flask


def create_app(config=None):
    app = Flask(__name__)

    @app.route('/hello')
    def hello():
        return 'hello, world'

    return app
