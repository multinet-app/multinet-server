"""Resolvers for entity type queries."""
from multinet import db
from multinet.types import Property


def name(entity_type, info):
    """Return the name of a type."""
    return entity_type.table


def properties(entity_type, info):
    """Return the properties of a type."""
    props = db.type_properties(entity_type.workspace, entity_type.graph, entity_type.table)
    return [Property(prop['label'], prop['table'], prop['key']) for prop in props]


def add_resolvers(schema):
    """Add the entity type resolvers to the schema object."""
    fields = schema.get_type('EntityType').fields
    fields['name'].resolver = name
    fields['properties'].resolver = properties
