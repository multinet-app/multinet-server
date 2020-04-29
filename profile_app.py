"""Profiles the application."""

from werkzeug.middleware.profiler import ProfilerMiddleware
from multinet.app import app

app.config["PROFILE"] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
app.run(debug=True)
