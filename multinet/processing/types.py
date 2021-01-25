"""Types used when processing multinet data."""
from typing import Dict, Callable, Union, Optional

TableRowEntry = Optional[Union[str, float, int, bool]]
TableRowEntryProcessor = Callable[[str], TableRowEntry]
UnprocessedTableRow = Dict[str, str]
ProcessedTableRow = Dict[str, TableRowEntry]
