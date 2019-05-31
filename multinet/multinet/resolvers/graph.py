from multinet import db
from multinet.types import EntityQuery

# a graph knows about the types of things in it and a set of nodes and edges


# each edge type is a set of keys that can be pulled from various tables
# that represent the possible properties of that edge
def edge_types(graph, info):
    return db.graph_edge_types(graph)


# each node type is a set of keys that can be pulled from various tables
# that represent the possible properties of that node
def node_types(graph, info):
    return db.graph_node_types(graph)


def name(graph, info):
    return graph.graph


def nodes(graph, info, nodeType=None, key=None, search=None):
    return EntityQuery(graph.workspace, graph.graph, nodeType, key, search)


def edges(graph, info, key=None, search=None):
    return EntityQuery(graph.workspace, graph.graph, None, key, search)


def add_resolvers(schema):
    fields = schema.get_type('Graph').fields
    fields['name'].resolver = name
    fields['edgeTypes'].resolver = edge_types
    fields['nodeTypes'].resolver = node_types
    fields['nodes'].resolver = nodes
    fields['edges'].resolver = edges
