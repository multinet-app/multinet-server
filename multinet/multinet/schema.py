"""A module to read in a MultiNet GraphQL schema, along with the resolvers."""
import os.path

from graphql import build_ast_schema
from graphql.language.parser import parse

from .resolvers import (
    attribute,
    properties,
    entity_type,
    entity,
    pagedlist,
    table,
    graph,
    workspace,
    query
)

schema_text = None
with open(os.path.join(os.path.dirname(__file__), 'multinet.gql')) as f:
    schema_text = f.read()

schema = build_ast_schema(parse(schema_text))

attribute.add_resolvers(schema)
properties.add_resolvers(schema)
entity_type.add_resolvers(schema)
entity.add_resolvers(schema)
pagedlist.add_resolvers(schema)
table.add_resolvers(schema)
graph.add_resolvers(schema)
workspace.add_resolvers(schema)
query.add_resolvers(schema)
