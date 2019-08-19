"""Resolvers for top level queries in GraphQL interface."""
from multinet import db
from multinet.types import Graph, Table


def workspaces(root, info, name=""):
    """Return list of workspace names accessible to the user."""
    return [
        workspace
        for workspace in db.get_workspaces(name)
        if not name or workspace == name
    ]


def graphs(root, info, workspace, name=""):
    """Return a list of graphs in a workspace."""
    return [
        Graph(workspace, graph)
        for graph in db.workspace_graphs(workspace)
        if not name or graph == name
    ]


def graph(root, info, workspace, name):
    """Return a single graph by workspace and name."""
    return Graph(workspace, name) if db.workspace_graph(workspace, name) else None


def tables(root, info, workspace, name=""):
    """Return a list of tables in a workspace."""
    return [
        Table(workspace, table)
        for table in db.workspace_tables(workspace)
        if not name or table == name
    ]


def table(root, info, workspace, name):
    """Return a specific table by workspace and name."""
    return Table(workspace, name) if db.workspace_table(workspace, name) else None


def add_resolvers(schema):
    """Add query resolvers to the schema object."""
    fields = schema.get_type("Query").fields
    fields["workspaces"].resolver = workspaces
    fields["graphs"].resolver = graphs
    fields["graph"].resolver = graph
    fields["tables"].resolver = tables
    fields["table"].resolver = table
