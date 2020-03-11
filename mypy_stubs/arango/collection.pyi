from arango.cursor import Cursor  # type: ignore
from arango.exceptions import ArangoError  # type: ignore
from typing import Any, Optional, Dict, Union, List

class Collection:
    def count(self) -> int: ...
    def has(
        self, document: Any, rev: Optional[Any] = ..., check_rev: bool = ...
    ) -> bool: ...
    def keys(self) -> Cursor: ...
    def all(self, skip: Optional[Any] = ..., limit: Optional[Any] = ...) -> Cursor: ...
    def find(self, filters: Dict, skip: int = None, limit: int = None) -> Cursor: ...
    def random(self) -> Dict: ...

class StandardCollection(Collection):
    def insert(
        self,
        document: Any,
        return_new: bool = ...,
        sync: Optional[Any] = ...,
        silent: bool = ...,
        overwrite: bool = ...,
        return_old: bool = ...,
    ) -> Union[bool, Dict]: ...
    def insert_many(
        self,
        documents: Any,
        return_new: bool = ...,
        sync: Optional[Any] = ...,
        silent: bool = ...,
        overwrite: bool = ...,
        return_old: bool = ...,
    ) -> List[Union[Dict, ArangoError]]: ...
    def delete(
        self,
        document: Dict,
        rev: Optional[str] = ...,
        check_rev: bool = ...,
        ignore_missing: bool = ...,
        return_old: bool = ...,
        sync: Optional[Any] = ...,
        silent: bool = ...,
    ) -> Union[Dict, bool]: ...
    def update(
        self,
        document: Dict,
        check_rev: bool = ...,
        merge: bool = ...,
        keep_none: bool = ...,
        return_new: bool = ...,
        return_old: bool = ...,
        sync: Optional[Any] = ...,
        silent: bool = ...,
    ) -> Union[Dict, bool]: ...

class VertexCollection(Collection): ...
class EdgeCollection(Collection): ...
