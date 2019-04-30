from multinet import db
from multinet.types import Graph, Table, EntityQuery, RowQuery

# get a list of workspaces a user has access to.
def workspaces(root, info, name=""):
    return [workspace for workspace in db.get_workspaces(name) if not name or workspace == name]

# get a list of graphs in a workspace
def graphs(root, info, workspace, name=""):
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace) if not name or graph == name]

# get a list of tables in a workspace
def tables(root, info, workspace, name=""):
    return [Table(workspace, table) for table in db.workspace_tables(workspace) if not name or table == name]

# get a list of nodes in a graph
def nodes(root, info, workspace, graph, nodeType=None, key=None, search=None):
    return EntityQuery(workspace, graph, nodeType, key, search)

# get a list of edges in a graph
def edges(root, info, workspace, graph, edgeType=None, key=None, search=None):
    return EntityQuery(workspace, graph, edgeType, key, search)

# get a list of rows in a table
def rows(root, info, workspace, table, key=None, search=None):
    return RowQuery(workspace, table, key, search)

def add_resolvers(schema):
    fields = schema.get_type('Query').fields
    fields['nodes'].resolver = nodes
    fields['edges'].resolver = edges
    fields['rows'].resolver = rows
    fields['workspaces'].resolver = workspaces
    fields['graphs'].resolver = graphs
    fields['tables'].resolver = tables
