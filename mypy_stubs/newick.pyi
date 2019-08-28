from typing import List


class Node:
    name: str
    descendants: List[Node]
    length: int


def loads(data: str) -> List[Node]: ...
