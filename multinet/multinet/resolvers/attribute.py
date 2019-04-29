# An attribute is simply a key-value pair. It represents a single cell in a table.
def add_resolvers(schema):
    fields = schema.get_type('Attribute').fields
    fields['key'].resolver = lambda attr, *_: attr.key
    fields['value'].resolver = lambda attr, *_: attr.value
