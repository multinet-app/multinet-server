from graphql import build_ast_schema
from graphql.language.parser import parse

from . import resolvers

schema = build_ast_schema(parse("""
    type Query {
        nodes(graph: String!, type: String="", id: String=""): [Node!]!
        edges(graph: String!, type: String="", id: String=""): [Edge!]!
    }

    type Attribute {
        key: String!
        value: String!
    }

    type Node {
        key: String!
        outgoing: [Edge!]
        incoming: [Edge!]
        attributes(source: String!, keys: [String!]): [Attribute!]
    }

    type Edge {
        key: String!
        source: Node!
        target: Node!
        attributes(source: String!, keys: [String!]): [Attribute!]
    }

    schema {
      query: Query
    }
"""))

fields = schema.get_type('Query').fields

fields['nodes'].resolver = resolvers.allNodes
fields['edges'].resolver = resolvers.allEdges

fields = schema.get_type('Node').fields
fields['key'].resolver = lambda node, *_: node[1]['_key']
fields['outgoing'].resolver = resolvers.nodeOutgoing
fields['incoming'].resolver = resolvers.nodeIncoming
fields['attributes'].resolver = resolvers.attributes

fields = schema.get_type('Edge').fields
fields['key'].resolver = lambda edge, *_: edge[1]['_key']
fields['source'].resolver = resolvers.edgeSource
fields['target'].resolver = resolvers.edgeTarget
fields['attributes'].resolver = resolvers.attributes

fields = schema.get_type('Attribute').fields
fields['key'].resolver = lambda attr, *_: attr[0]
fields['value'].resolver = lambda attr, *_: attr[1]
