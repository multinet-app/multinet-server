"""Resolvers for graph queries in GraphQL interface."""
from multinet import db
from multinet.types import EntityQuery


def edge_types(graph, info):
    """
    Return the edge types present for graph `graph`.

    Each edge type is a set of keys that can be pulled from various tables
    that represent the possible properties of that edge.
    """
    return db.graph_edge_types(graph)


def node_types(graph, info):
    """
    Return the node types present for graph `graph`.

    Each node type is a set of keys that can be pulled from various tables
    that represent the possible properties of that node.
    """
    return db.graph_node_types(graph)


def name(graph, info):
    """Return the name of graph `graph`."""
    return graph.graph


def nodes(graph, info, nodeType=None, key=None, search=None):
    """
    Perform a node query for graph `graph`.

    This query can be restricted to a specific `nodeType`, `key`, or `search`
    parameters.

    Currently, `search` is not implemented and has no effect on the query.
    """
    return EntityQuery(graph.workspace, graph.graph, nodeType, key, search)


def edges(graph, info, key=None, search=None):
    """
    Perform an edge query for graph `graph`.

    This query can be restricted to a specific `key` or `search` parameters.

    Currently, `search` is not implemented and has no effect on the query.
    """
    return EntityQuery(graph.workspace, graph.graph, None, key, search)


def add_resolvers(schema):
    """Add graph resolvers to the schema object."""
    fields = schema.get_type('Graph').fields
    fields['name'].resolver = name
    fields['edgeTypes'].resolver = edge_types
    fields['nodeTypes'].resolver = node_types
    fields['nodes'].resolver = nodes
    fields['edges'].resolver = edges
