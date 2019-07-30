from flask import Flask
from flask.logging import default_handler

from . import multinet


def create_app(config=None):
    print(__name__)
    app = Flask(__name__)

    # Set up logging.
    app.logger.addHandler(default_handler)

    # Register blueprints.
    app.register_blueprint(multinet.bp)

    @app.route('/hello')
    def hello():
        app.logger.debug('heyo')
        return 'hello, world'

    return app
