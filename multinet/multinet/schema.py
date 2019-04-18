from graphql import build_ast_schema
from graphql.language.parser import parse

from . import resolvers

schema = build_ast_schema(parse("""
    type Query {
        nodes (workspace: String!, graph: String!, nodeType: String, key: String, search: String): NodeList!
        edges (workspace: String!, graph: String!, edgeType: String, key: String, search: String): EdgeList!
        rows (workspace: String!, table: String!, key: String, search: String): RowList!

        workspaces (name: String): [Workspace!]!
        graphs (workspace: String!, name: String): [Graph!]!
        tables (workspace: String!, name: String): [Table!]!
    }

    type Mutation {
        workspace (name: String!): String!
        graph (workspace: String!, name: String!, nodeTypes: [String!]!, edgeTypes: [String!]!): Graph!
        table (workspace: String!, name: String!, fields: [String!]!, primaryKey: String): Table!
    }

    type NodeList {
        total: Int!
        nodes (offset: Int, limit: Int): [Node!]!
    }

    type EdgeList {
        total: Int!
        edges (offset: Int, limit: Int): [Edge!]!
    }

    type RowList {
        total: Int!
        rows (offset: Int, limit: Int): [Row!]!
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
        rows: RowList!
    }

    type Row {
        key: String!
        columns (keys: [String!]): [Attribute!]!
    }

    type Graph {
        name: String!
        nodeTypes: [String!]!
        edgeTypes: [String!]!
        nodes: NodeList!
        edges: EdgeList!
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
        properties (keys: [String!]): [Attribute!]
    }

    type Node implements Entity {
        key: String!
        type: EntityType!
        outgoing (limit: Int, offset: Int): EdgeList!
        incoming (limit: Int, offset: Int): EdgeList!
        properties (keys: [String!]): [Attribute!]
    }

    type Edge implements Entity {
        key: String!
        type: EntityType!
        source: Node!
        target: Node!
        properties (keys: [String!]): [Attribute!]
    }

    schema {
      query: Query
      mutation: Mutation
    }
"""))

fields = schema.get_type('Query').fields
fields['nodes'].resolver = resolvers.query_nodes
fields['edges'].resolver = resolvers.query_edges
fields['rows'].resolver = resolvers.query_rows
fields['workspaces'].resolver = resolvers.query_workspaces
fields['graphs'].resolver = resolvers.query_graphs
fields['tables'].resolver = resolvers.query_tables

fields = schema.get_type('Workspace').fields
fields['name'].resolver = resolvers.workspace_name
fields['tables'].resolver = resolvers.workspace_tables
fields['graphs'].resolver = resolvers.workspace_graphs

fields = schema.get_type('Table').fields
fields['name'].resolver = resolvers.table_name
fields['primaryKey'].resolver = lambda *_: '_id'
fields['fields'].resolver = resolvers.table_fields
fields['rows'].resolver = resolvers.table_rows

fields = schema.get_type('Graph').fields
fields['name'].resolver = resolvers.graph_name
fields['edgeTypes'].resolver = resolvers.edgeTypes
fields['nodeTypes'].resolver = resolvers.nodeTypes
fields['nodes'].resolver = resolvers.graph_nodelist
fields['edges'].resolver = resolvers.graph_edgelist

fields = schema.get_type('Node').fields
fields['key'].resolver = lambda node, *_: node['_id']
fields['type'].resolver = lambda node, *_: node['_type']
fields['outgoing'].resolver = resolvers.nodeOutgoing
fields['incoming'].resolver = resolvers.nodeIncoming
fields['properties'].resolver = resolvers.attributes

fields = schema.get_type('Edge').fields
fields['key'].resolver = lambda edge, *_: edge['_id']
fields['type'].resolver = lambda edge, *_: node['_type']
fields['source'].resolver = resolvers.edgeSource
fields['target'].resolver = resolvers.edgeTarget
fields['properties'].resolver = resolvers.attributes

fields = schema.get_type('Row').fields
fields['key'].resolver = lambda row, *_: row['_id']
fields['columns'].resolver = resolvers.attributes

fields = schema.get_type('Attribute').fields
fields['key'].resolver = lambda attr, *_: attr[0]
fields['value'].resolver = lambda attr, *_: attr[1]

fields = schema.get_type('NodeList').fields
fields['total'].resolver = resolvers.nodeCount
fields['nodes'].resolver = resolvers.nodes

fields = schema.get_type('EdgeList').fields
fields['total'].resolver = resolvers.edgeCount
fields['edges'].resolver = resolvers.edges

fields = schema.get_type('RowList').fields
fields['total'].resolver = resolvers.rowCount
fields['rows'].resolver = resolvers.rows

fields = schema.get_type('Mutation').fields
fields['workspace'].resolver = resolvers.create_workspace
fields['graph'].resolver = resolvers.create_graph
