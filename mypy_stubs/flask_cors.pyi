from flask import Flask

from typing import Dict, Any, List, Union

def CORS(
    app: Flask,
    origins: Union[str, List[str]],
    supports_credentials: bool,
    resources: Dict[str, Dict[str, Any]] = None,
) -> None: ...
