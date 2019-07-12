"""
Resolvers for paged queries in the GraphQL interface.

Paged lists allow the ui to specify a limit to the number of entities (nodes,
edges, rows) that are returned at once. In each case, an offset and limit value
can be specified.  for any given list, the total number of entities that could
have been returned can also be computed.

Each of these functions relies on receiving a "query". Each query indicates what
kind of filtering or search criteria should be used to determine what the
original list should be returning. However, in some cases, the list will have
been already fetched, in which case a "realized query" can be passed in which
contains the full list of entities already
"""
from multinet import db
from multinet.types import RealizedQuery, Cursor


def node_count(query, info):
    """Return the node count associated with a query."""
    return db.countNodes(query)


def nodes(query, info, offset=0, limit=10):
    """Retrieve a page of nodes for a particular query."""
    if type(query) == RealizedQuery:
        return query.values[offset:(offset + limit)]
    return db.fetchNodes(query, Cursor(offset, limit))


def edge_count(query, info):
    """Return the edge count associated with a query."""
    if type(query) == RealizedQuery:
        return len(query.values)
    return db.countEdges(query)


def edges(query, info, offset=0, limit=10):
    """Retrieve a page of edges for a particular query."""
    if type(query) == RealizedQuery:
        return query.values[offset:(offset + limit)]
    return db.fetchEdges(query, Cursor(offset, limit))


def row_count(query, info):
    """Return the row count associated with a query."""
    if type(query) == RealizedQuery:
        return len(query.values)
    return db.countRows(query)


def rows(query, info, offset=0, limit=10):
    """Retrieve a page of rows for a particular query."""
    return db.fetchRows(query, Cursor(offset, limit))


def add_resolvers(schema):
    """Add the paged query resolvers to the schema object."""
    fields = schema.get_type('RowList').fields
    fields['total'].resolver = row_count
    fields['data'].resolver = rows

    fields = schema.get_type('NodeList').fields
    fields['total'].resolver = node_count
    fields['data'].resolver = nodes

    fields = schema.get_type('EdgeList').fields
    fields['total'].resolver = edge_count
    fields['data'].resolver = edges
