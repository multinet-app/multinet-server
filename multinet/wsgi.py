"""Stub wsgi application for production deployment."""
from multinet.app import app as application

if __name__ == "__main__":
    application.run()
