from multinet import db
from multinet.types import RowQuery

# A table is a raw block of data that is not directly associated with a graph.
# Each table has a logical set of fields and rows.


def rows(table, info, key=None, search=None):
    return RowQuery(table.workspace, table.table, key, search)


def name(table, info):
    return table.table


def _fields(table, info):
    return db.table_fields(table)


def add_resolvers(schema):
    fields = schema.get_type('Table').fields
    fields['name'].resolver = name
    fields['primaryKey'].resolver = lambda *_: '_id'
    fields['fields'].resolver = _fields
    fields['rows'].resolver = rows
