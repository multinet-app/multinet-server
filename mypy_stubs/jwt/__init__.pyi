from typing import Union, Dict, Mapping, Optional, Callable, List, Any

def encode(
    payload: Union[Mapping, bytes],
    key: str,
    algorithm: str = ...,
    headers: Optional[Mapping] = ...,
    json_encoder: Optional[Callable] = ...,
) -> Any: ...
def decode(
    jwt: str,
    key: str = ...,
    verify: bool = ...,
    algorithms: List[str] = ...,
    options: Mapping = ...,
    **kwargs: Any
) -> Any: ...
