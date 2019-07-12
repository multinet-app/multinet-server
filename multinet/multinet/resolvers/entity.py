"""Resolvers for entity queries in GraphQL interface."""
from multinet import db
from multinet.types import Attribute, RealizedQuery, EntityType


def attributes(entity, info, keys=None):
    """
    Return the attribute data associated with an entity.

    Entities are nodes, edges, and rows. Entities share in common having a
    single key and a set of key-value pairs. Each key-value pair represents a
    property on nodes and edges or a cell on a row.
    """
    return [
        Attribute(key, value)
        for key, value in entity.data.items()
        if (keys is None) or (key in keys)
    ]


def outgoing(node, info):
    """Return the outgoing edges of a node."""
    return RealizedQuery(db.outgoing(node))


def incoming(node, info):
    """Return the incoming edges of a node."""
    return RealizedQuery(db.incoming(node))


def source(edge, info):
    """Return the source node of an edge."""
    return db.source(edge)


def target(edge, info):
    """Return the target node of an edge."""
    return db.target(edge)


def entity_type(entity, info):
    """Return the entity type."""
    return EntityType(entity.workspace, entity.graph, entity.entity_type)


def add_resolvers(schema):
    """Add the entity resolvers to the schema object."""
    fields = schema.get_type('Node').fields
    fields['key'].resolver = lambda node, *_: node.data['_id']
    fields['type'].resolver = entity_type
    fields['outgoing'].resolver = outgoing
    fields['incoming'].resolver = incoming
    fields['properties'].resolver = attributes

    fields = schema.get_type('Edge').fields
    fields['key'].resolver = lambda edge, *_: edge.data['_id']
    fields['type'].resolver = entity_type
    fields['source'].resolver = source
    fields['target'].resolver = target
    fields['properties'].resolver = attributes

    fields = schema.get_type('Row').fields
    fields['key'].resolver = lambda row, *_: row.data['_id']
    fields['columns'].resolver = attributes
