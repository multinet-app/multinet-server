import os.path

from graphql import build_ast_schema
from graphql.language.parser import parse

from . import resolvers

schema_text = None
with open(os.path.join(os.path.dirname(__file__), 'multinet.gql')) as f:
    schema_text = f.read()

schema = build_ast_schema(parse(schema_text))

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
fields['key'].resolver = lambda node, *_: node.data['_id']
fields['type'].resolver = lambda node, *_: node.entity_type
fields['outgoing'].resolver = resolvers.nodeOutgoing
fields['incoming'].resolver = resolvers.nodeIncoming
fields['properties'].resolver = resolvers.attributes

fields = schema.get_type('Edge').fields
fields['key'].resolver = lambda edge, *_: edge.data['_id']
fields['type'].resolver = lambda edge, *_: edge.entity_type
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
