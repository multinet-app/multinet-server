from typing import Any


class ArangoClient:
    def __init__(self, host: str, port: int): ...

    def db(self, database: str, username: str, password: str) -> Any: ...
