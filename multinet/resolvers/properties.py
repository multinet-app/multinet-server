"""Resolvers for property queries in the GraphQL interface."""


def label(prop, info):
    """Return the display label for a property."""
    return prop.label


def table(prop, info):
    """Return the table associated with a property."""
    return prop.table


def key(prop, info):
    """Return the column name for a property."""
    return prop.key


def add_resolvers(schema):
    """Add the property resolvers to the schema object."""
    fields = schema.get_type("Property").fields
    fields["label"].resolver = label
    fields["table"].resolver = table
    fields["key"].resolver = key
