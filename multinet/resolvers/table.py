"""
Resolvers for table queries in GraphQL interface.

A table is a raw block of data that is not directly associated with a graph.
Each table has a logical set of fields and rows.
"""
from multinet import db
from multinet.types import RowQuery


def rows(table, info, key=None, search=None):
    """Return a row query object subject to further queries."""
    return RowQuery(table.workspace, table.table, key, search)


def name(table, info):
    """Return the name of a table."""
    return table.table


def _fields(table, info):
    """Return the fields of a table."""
    return db.table_fields(table)


def add_resolvers(schema):
    """Add table resolvers to the schema object."""
    fields = schema.get_type("Table").fields
    fields["name"].resolver = name
    fields["primaryKey"].resolver = lambda *_: "_id"
    fields["fields"].resolver = _fields
    fields["rows"].resolver = rows
