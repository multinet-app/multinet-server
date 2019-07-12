"""Mutation queries for GraphQL interface."""
from multinet import db
from multinet.types import Graph, Table


def workspace(root, info, name):
    """Create a workspace."""
    db.create_workspace(name)
    return name


def delete_workspace(root, info, name):
    """Delete a workspace."""
    return name if db.delete_workspace(name) else None


def graph(root, info, workspace, name, node_tables, edge_table):
    """Create a graph."""
    graph = Graph(workspace, name)
    return graph if db.create_graph(graph, node_tables, edge_table) else None


def table(root, info, workspace, name, edges=False, primaryKey='_id', fields=None):
    """Create a table."""
    if fields is None:
        fields = []

    table = Table(workspace, name)
    db.create_table(table, edges)
    return table


def add_resolvers(schema):
    """Add the mutation resolvers to the schema object."""
    fields = schema.get_type('Mutation').fields
    fields['workspace'].resolver = workspace
    fields['deleteWorkspace'].resolver = delete_workspace
    fields['graph'].resolver = graph
    fields['table'].resolver = table
