from typing import Dict, Optional, Union
from arango.connection import Connection  # type: ignore
from arango.executor import Executor  # type: ignore
from arango.cursor import Cursor

class AQL:
    """AQL (ArangoDB Query Language) API wrapper.

    :param connection: HTTP connection.
    :type connection: arango.connection.Connection
    :param executor: API executor.
    :type executor: arango.executor.Executor
    """

    def __init__(self, connection: Connection, executor: Executor): ...
    def validate(self, query: str) -> Dict: ...
    def execute(
        self,
        query: str,
        count: bool = False,
        batch_size: Optional[int] = None,
        ttl: Optional[int] = None,
        bind_vars: Optional[Dict] = None,
        full_count: Optional[bool] = None,
        max_plans: Optional[int] = None,
        optimizer_rules: Optional[str] = None,
        cache: Optional[bool] = None,
        memory_limit: int = 0,
        fail_on_warning: Optional[bool] = None,
        profile: Optional[bool] = None,
        max_transaction_size: Optional[int] = None,
        max_warning_count: Optional[int] = None,
        intermediate_commit_count: Optional[int] = None,
        intermediate_commit_size: Optional[int] = None,
        satellite_sync_wait: Optional[Union[int, float]] = None,
        read_collections: Optional[str] = None,
        write_collections: Optional[str] = None,
        stream: Optional[bool] = None,
        skip_inaccessible_cols: Optional[bool] = None,
    ) -> Cursor: ...
