"""A mdoule holding the named tuple types used in the GraphQL schema."""
from collections import namedtuple

# key and value are both strings meant to represent a single cell of data.
Attribute = namedtuple('Attribute', ['key', 'value'])

# workspace, table, graph, and entity_type are all strings meant to indicate
# where the data was found in case additional related data needs to be fetched.
# the data value in each of these cases is a dictionary of cell-level data
Row = namedtuple('Row', ['workspace', 'table', 'data'])
Entity = namedtuple('Entity', ['workspace', 'graph', 'entity_type', 'data'])

# workspace, table, and graph are all strings to orient the database towards
# data that needs to be fetched.
Table = namedtuple('Table', ['workspace', 'table'])
Graph = namedtuple('Graph', ['workspace', 'graph'])

# label, table, key, workspace, graph, and name are all strings. properties is a
# list of Property objects.
Property = namedtuple('Property', ['label', 'table', 'key'])
EntityType = namedtuple('EntityType', ['workspace', 'graph', 'table'])

# numerical values representing where to start in a list of nodes/edges/rows and
# how many to return
Cursor = namedtuple('Cursor', ['offset', 'limit'])

# string values representing what filters and search criteria to apply
EntityQuery = namedtuple('EntityQuery', ['workspace', 'graph', 'entity_type', 'id', 'search'])
RowQuery = namedtuple('RowQuery', ['workspace', 'table', 'id', 'search'])

# an already fetched list that can be passed into the paging functionality
RealizedQuery = namedtuple('RealizedQuery', ['values'])
