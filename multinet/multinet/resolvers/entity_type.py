def name(entity_type, info):
    return entity_type.name

def properties(entity_type, info):
    return [prop for prop in entity_type.properties]

def add_resolvers(schema):
    fields = schema.get_type('EntityType').fields
    fields['name'].resolver = name
    fields['properties'].resolver = properties
