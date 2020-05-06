from flask import Flask

from typing import Dict, Any

def CORS(app: Flask, resources: Dict[str, Dict[str, Any]]) -> None: ...
