from graphql import build_ast_schema
from graphql.language.parser import parse

from . import resolvers

schema = build_ast_schema(parse("""
    type Query {
        nodes (workspace: String!, graph: String!, nodeType: String, key: String, search: String, limit: Int, offset: Int): NodeCursor!
        edges (workspace: String!, graph: String!, edgeType: String, key: String, search: String, limit: Int, offset: Int): EdgeCursor!
        rows (workspace: String!, table: String!, key: String, search: String, limit: Int, offset: Int): RowCursor!

        workspaces (name: String): [Workspace!]!
        graphs (workspace: String!, name: String): [Graph!]!
        tables (workspace: String!, name: String): [Table!]!
    }

    type Mutation {
        workspace (name: String!): String!
        graph (workspace: String!, name: String!, nodeTables: [String!]!, edgeTables: [String!]!): Graph!
        table (workspace: String!, name: String!, primaryKey: String="_id", fields: [String!]!): Table!
    }

    interface Cursor {
        limit: Int!
        offset: Int!
        total: Int!
    }

    type NodeCursor implements Cursor {
        limit: Int!
        offset: Int!
        total: Int!
        nodes: [Node!]!
    }

    type EdgeCursor implements Cursor {
        limit: Int!
        offset: Int!
        total: Int!
        edges: [Edge!]!
    }

    type RowCursor implements Cursor {
        limit: Int!
        offset: Int!
        total: Int!
        row: [Row!]!
    }

    type Attribute {
        # the key is the table name followed by the column name delimited by a slash, eg table/col
        key: String!
        # json representation of the value
        value: String!
    }

    type Table {
        name: String!
        primaryKey: String!
        # a list of key strings as they would appear in Attribute
        fields: [String!]!
        rows (limit: Int, offset: Int): RowCursor!
    }

    type Row {
        key: String!
        columns: [Attribute!]!
    }

    type Graph {
        name: String!
        nodeTypes: [EntityType!]!
        edgeTypes: [EntityType!]!
        nodes (offset: Int!, limit: Int!): NodeCursor!
        edges (offset: Int!, limit: Int!): EdgeCursor!
    }

    type EntityType {
        name: String!
        properties: [Property!]!
    }

    type Property {
        label: String!
        key: String!
    }

    type Workspace {
        name: String!
        tables: [Table!]!
        graphs: [Graph!]!
    }

    interface Entity {
        # this is the id of the entity in all tables it's associated with
        key: String!
        type: EntityType!
        attributes (source: String!, keys: [String!]): [Attribute!]
    }

    type Node implements Entity {
        key: String!
        type: EntityType!
        outgoing (limit: Int, offset: Int): EdgeCursor!
        incoming (limit: Int, offset: Int): EdgeCursor!
        attributes (keys: [String!]): [Attribute!]
    }

    type Edge implements Entity {
        key: String!
        type: EntityType!
        source: Node!
        target: Node!
        attributes (keys: [String!]): [Attribute!]
    }

    schema {
      query: Query
      mutation: Mutation
    }
"""))

fields = schema.get_type('Query').fields
fields['nodes'].resolver = resolvers.query_nodes
fields['edges'].resolver = resolvers.query_edges
fields['workspaces'].resolver = resolvers.query_workspaces
fields['graphs'].resolver = resolvers.query_graphs
fields['tables'].resolver = resolvers.query_tables

fields = schema.get_type('Workspace').fields
fields['name'].resolver = resolvers.workspace_name
fields['tables'].resolver = resolvers.workspace_tables
fields['graphs'].resolver = resolvers.workspace_graphs

fields = schema.get_type('Table').fields
fields['name'].resolver = resolvers.table_name
fields['primaryKey'].resolver = lambda *_: '_key'
fields['fields'].resolver = resolvers.table_fields

fields = schema.get_type('Graph').fields
fields['name'].resolver = resolvers.graph_name
fields['edgeTables'].resolver = resolvers.graph_edgeTables
fields['nodeTables'].resolver = resolvers.graph_nodeTables
fields['nodes'].resolver = resolvers.graph_nodes
fields['edges'].resolver = resolvers.graph_edges

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

fields = schema.get_type('NodeCursor').fields
fields['offset'].resolver = lambda cursor, *_: cursor['offset']
fields['limit'].resolver = lambda cursor, *_: cursor['limit']
fields['total'].resolver = lambda cursor, *_: cursor['total']
fields['nodes'].resolver = lambda cursor, *_: cursor['nodes']

fields = schema.get_type('EdgeCursor').fields
fields['offset'].resolver = lambda cursor, *_: cursor['offset']
fields['limit'].resolver = lambda cursor, *_: cursor['limit']
fields['total'].resolver = lambda cursor, *_: cursor['total']
fields['edges'].resolver = lambda cursor, *_: cursor['edges']

fields = schema.get_type('Mutation').fields
fields['workspace'].resolver = resolvers.create_workspace
fields['graph'].resolver = resolvers.create_graph
