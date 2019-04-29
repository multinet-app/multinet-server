from . import db
from .types import *

# a workspace is a representation of tables and graphs that are inter-related and
# potentially co-accessible.

def workspace_name(workspace, info):
    return workspace

def workspace_tables(workspace, info):
    return [Table(workspace, table) for table in db.workspace_tables(workspace)]

def workspace_graphs(workspace, info):
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace)]

def add_resolvers(schema):
    fields = schema.get_type('Workspace').fields
    fields['name'].resolver = workspace_name
    fields['tables'].resolver = workspace_tables
    fields['graphs'].resolver = workspace_graphs
