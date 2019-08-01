"""Flask factory for Multinet app."""
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS

from . import multinet


def create_app(config=None):
    """Create a Multinet app instance."""
    app = Flask(__name__)
    CORS(app)

    # Set up logging.
    app.logger.addHandler(default_handler)

    # Register blueprints.
    app.register_blueprint(multinet.bp, url_prefix='/multinet')

    @app.route('/about')
    def about():
        return '''
            <h1>Multinet API</h1>
            <div>
                See <a href="https://multinet.app">Multinet website</a> for details.
            </div>
        '''

    return app
