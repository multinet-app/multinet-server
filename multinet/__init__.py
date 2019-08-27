"""Flask factory for Multinet app."""
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS

from . import api
from . import uploaders
from .errors import ServerError


def create_app(config=None):
    """Create a Multinet app instance."""
    app = Flask(__name__)
    CORS(app)

    # Set up logging.
    app.logger.addHandler(default_handler)

    # Register blueprints.
    app.register_blueprint(api.bp, url_prefix="/api")
    app.register_blueprint(uploaders.csv.bp, url_prefix="/api/csv")
    app.register_blueprint(uploaders.newick.bp, url_prefix="/api/newick")
    app.register_blueprint(uploaders.nested_json.bp, url_prefix="/api/nested_json")

    # Register error handler.
    @app.errorhandler(ServerError)
    def handle_error(error):
        return error.flask_response()

    @app.route("/")
    def about():
        return """
            <h1>Multinet API</h1>
            <div>
                See <a href="https://multinet.app">Multinet website</a> for details.
            </div>
        """

    return app
