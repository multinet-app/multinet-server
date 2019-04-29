from . import db
from .types import *

# A table is a raw block of data that is not directly associated with a graph.
# Each table has a logical set of fields and rows. 

def table_rows(table, info):
    return RowQuery(table.workspace, table.table, None, None)

def table_name(table, info):
    return table.table

def table_fields(table, info):
    return db.table_fields(table)

def add_resolvers(schema):
    fields = schema.get_type('Table').fields
    fields['name'].resolver = table_name
    fields['primaryKey'].resolver = lambda *_: '_id'
    fields['fields'].resolver = table_fields
    fields['rows'].resolver = table_rows
