"""
Resolvers for workspace queries in GraphQL interface.

A workspace is a representation of tables and graphs that are inter-related and
potentially co-accessible.
"""
from multinet import db
from multinet.types import Table, Graph


def name(workspace, info):
    """Return the name of a workspace."""
    print('PPPP', workspace, info.field_name)
    return workspace


def tables(workspace, info):
    """Return the tables within a workspace."""
    return [Table(workspace, table) for table in db.workspace_tables(workspace)]


def graphs(workspace, info):
    """Return the graphs within a workspace."""
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace)]


def add_resolvers(schema):
    """Add workspace resolvers to the schema object."""
    fields = schema.get_type('Workspace').fields
    fields['name'].resolver = name
    fields['tables'].resolver = tables
    fields['graphs'].resolver = graphs
