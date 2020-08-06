from arango.cursor import Cursor  # type: ignore
from arango.exceptions import ArangoError  # type: ignore
from typing import Any, Optional, Dict, Union, List, Mapping

class Collection:
    def count(self) -> int: ...
    def has(
        self, document: Any, rev: Optional[Any] = ..., check_rev: bool = ...
    ) -> bool: ...
    def keys(self) -> Cursor: ...
    def all(self, skip: Optional[Any] = ..., limit: Optional[Any] = ...) -> Cursor: ...
    def find(self, filters: Dict, skip: int = None, limit: int = None) -> Cursor: ...
    def get(
        self,
        document: Union[Dict, str],
        rev: Optional[str] = None,
        check_rev: bool = True,
    ) -> Dict: ...
    def random(self) -> Dict: ...

class StandardCollection(Collection):
    name: str

    def insert(
        self,
        document: Any,
        return_new: bool = ...,
        sync: Optional[Any] = ...,
        overwrite: bool = ...,
        return_old: bool = ...,
    ) -> Dict: ...
    def insert_many(
        self,
        documents: Any,
        return_new: bool = ...,
        sync: Optional[Any] = ...,
        overwrite: bool = ...,
        return_old: bool = ...,
    ) -> List[Union[Dict, ArangoError]]: ...
    def delete(
        self,
        document: Union[Dict, str],
        rev: Optional[str] = ...,
        check_rev: bool = ...,
        ignore_missing: bool = ...,
        return_old: bool = ...,
        sync: Optional[Any] = ...,
    ) -> Dict: ...
    def update(
        self,
        document: Union[Mapping[str, Any], str],
        check_rev: bool = ...,
        merge: bool = ...,
        keep_none: bool = ...,
        return_new: bool = ...,
        return_old: bool = ...,
        sync: Optional[Any] = ...,
    ) -> Dict: ...
    def properties(self) -> Dict: ...

class VertexCollection(Collection): ...
class EdgeCollection(Collection): ...
