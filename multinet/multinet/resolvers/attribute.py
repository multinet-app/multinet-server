"""Resolvers for attribute queries."""


def add_resolvers(schema):
    """
    Add the key and value resolvers.

    An attribute is simply a key-value pair. It represents a single cell in a
    table.
    """
    fields = schema.get_type('Attribute').fields
    fields['key'].resolver = lambda attr, *_: attr.key
    fields['value'].resolver = lambda attr, *_: attr.value
