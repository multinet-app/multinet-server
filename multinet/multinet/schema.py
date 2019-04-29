import os.path

from graphql import build_ast_schema
from graphql.language.parser import parse

from . import attribute
from . import entity
from . import pagedlist
from . import table
from . import graph
from . import workspace
from . import query
from . import mutation

schema_text = None
with open(os.path.join(os.path.dirname(__file__), 'multinet.gql')) as f:
    schema_text = f.read()

schema = build_ast_schema(parse(schema_text))

attribute.add_resolvers(schema)
entity.add_resolvers(schema)
pagedlist.add_resolvers(schema)
table.add_resolvers(schema)
graph.add_resolvers(schema)
workspace.add_resolvers(schema)
query.add_resolvers(schema)
mutation.add_resolvers(schema)
