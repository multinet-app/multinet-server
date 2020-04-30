from flask import Flask
from werkzeug.local import LocalProxy
from authlib.integrations.base_client import BaseOAuth  # type: ignore
from typing import Dict, Any, Callable

class OAuth:
    def __init__(self) -> None: ...
    def init_app(
        self,
        app: Flask = None,
        cache: Any = None,  # Cache should be a class that has the methods: get, set and delete
        fetch_token: Callable = None,
        update_token: Callable = None,
    ) -> None: ...
    def create_client(self, name: str) -> BaseOAuth: ...
    def register(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        access_token_url: str,
        authorize_url: str,
        api_base_url: str,
        client_kwargs: Dict,
    ) -> LocalProxy: ...
