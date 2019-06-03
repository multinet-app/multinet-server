def label(prop, info):
    return prop.label


def table(prop, info):
    return prop.table


def key(prop, info):
    return prop.key


def add_resolvers(schema):
    fields = schema.get_type('Property').fields
    fields['label'].resolver = label
    fields['table'].resolver = table
    fields['key'].resolver = key
