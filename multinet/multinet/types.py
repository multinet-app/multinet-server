from collections import namedtuple

# numerical values representing where to start in a list of nodes/edges/rows and how many to return
Cursor = namedtuple('Cursor', ['offset', 'limit'])

# all strings referring to the database name
Table = namedtuple('Table', ['workspace', 'table'])
Row = namedtuple('Entity', ['workspace', 'table', 'data'])

Graph = namedtuple('Graph', ['workspace', 'graph'])
EntityType = namedtuple('EntityType', ['workspace', 'graph', 'entity_type'])
Entity = namedtuple('Entity', ['workspace', 'graph', 'entity_type', 'data'])

#
EntityQuery = namedtuple('EntityQuery', ['workspace', 'graph', 'entity_type', 'id', 'search'])
RowQuery = namedtuple('RowQuery', ['workspace', 'table', 'id', 'search'])
RealizedQuery = namedtuple('RealizedQuery', ['values'])
