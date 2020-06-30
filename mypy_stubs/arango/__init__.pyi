from typing import Any

class ArangoClient:
    def __init__(self, host: str, port: int, protocol: str): ...
    def db(
        self,
        name: str = "_system",
        username: str = "root",
        password: str = "",
        verify: bool = False,
    ) -> Any: ...
