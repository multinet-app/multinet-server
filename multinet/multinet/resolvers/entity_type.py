from girder import logprint

from multinet import db
from multinet.types import Property

def name(entity_type, info):
    return entity_type.table

def properties(entity_type, info):
    props = db.type_properties(entity_type.workspace, entity_type.graph, entity_type.table)
    return [Property(prop['label'], prop['table'], prop['key']) for prop in props]

def add_resolvers(schema):
    fields = schema.get_type('EntityType').fields
    fields['name'].resolver = name
    fields['properties'].resolver = properties
