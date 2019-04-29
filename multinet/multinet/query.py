from . import db
from .types import *

# get a list of workspaces a user has access to.
def query_workspaces(root, info, name=""):
    return [workspace for workspace in db.get_workspaces(name) if not name or workspace == name]

# get a list of graphs in a workspace
def query_graphs(root, info, workspace, name=""):
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace) if not name or graph == name]

# get a list of tables in a workspace
def query_tables(root, info, workspace, name=""):
    return [Table(workspace, table) for table in db.workspace_tables(workspace) if not name or table == name]

# get a list of nodes in a graph
def query_nodes(root, info, workspace, graph, nodeType=None, key=None, search=None):
    return EntityQuery(workspace, graph, nodeType, key, search)

# get a list of edges in a graph
def query_edges(root, info, workspace, graph, edgeType=None, key=None, search=None):
    return EntityQuery(workspace, graph, edgeType, key, search)

# get a list of rows in a table
def query_rows(root, info, workspace, table, key=None, search=None):
    return RowQuery(workspace, table, key, search)

def add_resolvers(schema):
    fields = schema.get_type('Query').fields
    fields['nodes'].resolver = query_nodes
    fields['edges'].resolver = query_edges
    fields['rows'].resolver = query_rows
    fields['workspaces'].resolver = query_workspaces
    fields['graphs'].resolver = query_graphs
    fields['tables'].resolver = query_tables
