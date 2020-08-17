"""Flask factory for Multinet app."""
import os
import sentry_sdk
from flask import Flask
from flask.logging import default_handler
from flask_cors import CORS
from flasgger import Swagger
from sentry_sdk.integrations.flask import FlaskIntegration

from typing import Optional, MutableMapping, Any, Tuple, Union, List

from multinet import auth
from multinet.auth import google
from multinet import api
from multinet.db import register_legacy_workspaces
from multinet import uploaders, downloaders
from multinet.errors import ServerError
from multinet.util import flask_secret_key

sentry_dsn = os.getenv("SENTRY_DSN", default="")
sentry_sdk.init(dsn=sentry_dsn, integrations=[FlaskIntegration()])


def get_allowed_origins() -> List[str]:
    """Read in comma-separated list of allowed origins from environment."""
    allowed_origins = os.getenv("ALLOWED_ORIGINS", default=None)
    if allowed_origins is None:
        return []

    return [s.strip() for s in allowed_origins.split(",")]


def create_app(config: Optional[MutableMapping] = None) -> Flask:
    """Create a Multinet app instance."""
    app = Flask(__name__)

    if config is not None:
        app.config.update(config)

    allowed_origins = get_allowed_origins()
    CORS(app, origins=allowed_origins, supports_credentials=True)
    Swagger(app, template_file="swagger/template.yaml")

    # Set max file upload size to 32 MB
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

    app.secret_key = flask_secret_key()

    # Set up logging.
    app.logger.addHandler(default_handler)

    # Register blueprints.
    app.register_blueprint(api.bp, url_prefix="/api")
    app.register_blueprint(uploaders.csv.bp, url_prefix="/api/csv")
    app.register_blueprint(uploaders.newick.bp, url_prefix="/api/newick")
    app.register_blueprint(uploaders.nested_json.bp, url_prefix="/api/nested_json")
    app.register_blueprint(uploaders.d3_json.bp, url_prefix="/api/d3_json")

    app.register_blueprint(uploaders.multipart_upload.bp, url_prefix="/api/uploads")

    app.register_blueprint(downloaders.csv.bp, url_prefix="/api")
    app.register_blueprint(downloaders.d3_json.bp, url_prefix="/api")

    app.register_blueprint(auth.bp, url_prefix="/api/user")
    app.register_blueprint(google.bp, url_prefix="/api/user/oauth/google")

    google.init_oauth(app)
    register_legacy_workspaces()

    # Register error handler.
    @app.errorhandler(ServerError)
    def handle_error(error: ServerError) -> Tuple[Any, Union[int, str]]:
        return error.flask_response()

    @app.route("/")
    def about() -> str:
        return """
            <h1>Multinet API</h1>
            <div>
              <p>
                See <a href="https://multinet.app">Multinet website</a> for details.
              </p>

              <p>
                Check out the <a href="/apidocs">API documentation</a>.
              </p>
            </div>
        """

    return app
