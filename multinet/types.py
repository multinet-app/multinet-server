"""Custom types for Multinet codebase."""
from typing_extensions import Literal


EdgeDirection = Literal["all", "incoming", "outgoing"]
TableType = Literal["all", "node", "edge"]
