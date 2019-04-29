from multinet import db
from multinet.types import Table, Graph

# a workspace is a representation of tables and graphs that are inter-related and
# potentially co-accessible.

def name(workspace, info):
    return workspace

def tables(workspace, info):
    return [Table(workspace, table) for table in db.workspace_tables(workspace)]

def graphs(workspace, info):
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace)]

def add_resolvers(schema):
    fields = schema.get_type('Workspace').fields
    fields['name'].resolver = name
    fields['tables'].resolver = tables
    fields['graphs'].resolver = graphs
