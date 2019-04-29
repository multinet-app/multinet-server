from . import db
from .types import *

# The entities are nodes, edges, and rows. Entities share in common having a single
# key and a set of key-value pairs. Each key-value pair represents a property on
# nodes and edges or a cell on a row.
def attributes(entity, info, keys=None):
    return [Attribute(key, value) for key, value in entity.data.items() if (keys is None) or (key in keys)]

# computes the outgoing edges of a node
def outgoing(node, info):
    return RealizedQuery(db.outgoing(node))

# computes the incoming edges of a node
def incoming(node, info):
    return RealizedQuery(db.incoming(node))

# computes the source node of an edge
def source(edge, info):
    return db.source(edge)

# computes the target node of an edge
def target(edge, info):
    return db.target(edge)

def add_resolvers(schema):
    fields = schema.get_type('Node').fields
    fields['key'].resolver = lambda node, *_: node.data['_id']
    fields['type'].resolver = lambda node, *_: node.entity_type
    fields['outgoing'].resolver = outgoing
    fields['incoming'].resolver = incoming
    fields['properties'].resolver = attributes

    fields = schema.get_type('Edge').fields
    fields['key'].resolver = lambda edge, *_: edge.data['_id']
    fields['type'].resolver = lambda edge, *_: edge.entity_type
    fields['source'].resolver = source
    fields['target'].resolver = target
    fields['properties'].resolver = attributes

    fields = schema.get_type('Row').fields
    fields['key'].resolver = lambda row, *_: row.data['_id']
    fields['columns'].resolver = attributes
