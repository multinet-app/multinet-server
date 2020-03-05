"""This is the setup module for the multinet package."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

setup(
    author="MultiNet Team",
    author_email="multinet@multinet.app",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Multinet API",
    install_requires=[
        "python-arango",
        "newick",
        "uuid",
        "requests",
        "webargs",
        "flask",
        "flask-cors",
        "flasgger",
        "typing-extensions",
        "uwsgi",
        "sentry-sdk[flask]",
        "gunicorn",
    ],
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="multinet",
    name="multinet",
    packages=find_packages(exclude=["test", "test.*"]),
    url="https://github.com/multinet-app/multinet",
    version="0.1.0",
    zip_safe=False,
)
