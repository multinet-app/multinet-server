"""Functions for processing multinet data."""
from multinet.validation import (
    ValidationFailure,
    IncompatibleMetadata,
    MetadataColumnKeyNotFound,
)
from multinet.processing.processors import (
    process_number_entry,
    process_boolean_entry,
    process_date_entry,
)
from multinet.types import ColumnMetadata
from multinet.processing.types import (
    UnprocessedTableRow,
    ProcessedTableRow,
    TableRowEntryProcessor,
)

# Import types
from typing import List, Dict, Tuple


# Maps types to the functions responsible for processing their entries
entry_processing_dict: Dict[str, TableRowEntryProcessor] = {
    "number": process_number_entry,
    "boolean": process_boolean_entry,
    "date": process_date_entry,
}


def process_row(
    row_index: int, row: UnprocessedTableRow, columns: List[ColumnMetadata]
) -> Tuple[ProcessedTableRow, List[ValidationFailure]]:
    """Process a single row, returning the processed row, and any errors."""
    validation_errors: List[ValidationFailure] = []

    # Copy row
    new_row: ProcessedTableRow = dict(row)

    for col in columns:
        entry = row.get(col.key)

        # If any of the following conditions are met, skip processing the entry
        if entry is None:
            validation_errors.append(MetadataColumnKeyNotFound(key=col.key))
            continue

        process_entry = entry_processing_dict.get(col.type)
        if process_entry is None:
            # This happens on any type not defined in `entry_processing_dict`
            # E.g. label, category
            continue

        # Attempt normal entry processing
        try:
            # If the entry is an empty string, replace with None (null)
            processed_entry = process_entry(entry) if entry else None

            # Processing successful, update row entry with its new value
            new_row[col.key] = processed_entry
        except ValueError:
            # Error in processing entry. Add error, leave entry unchanged
            validation_errors.append(
                IncompatibleMetadata(
                    message=f"Cannot convert entry '{entry}' to type: {col.type}",
                    row=row_index,
                    column=col.key,
                )
            )

    return (new_row, validation_errors)


def process_rows(
    initial_rows: List[UnprocessedTableRow], col_metadata: List[ColumnMetadata]
) -> Tuple[List[ProcessedTableRow], List[ValidationFailure]]:
    """Perform any processing of table rows with the supplied metadata."""
    if not col_metadata or not initial_rows:
        # Copy rows to ensure consistent behavior, no change applied
        rows: List[ProcessedTableRow] = [dict(row) for row in initial_rows]
        return (rows, [])

    rows = []
    validation_errors: List[ValidationFailure] = []

    for i, init_row in enumerate(initial_rows):
        row, errors = process_row(i, init_row, col_metadata)

        rows.append(row)
        validation_errors.extend(errors)

    return (rows, validation_errors)
