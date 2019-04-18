import os
import logging
from girder import plugin, logprint
from types import *

from . import db

def query_workspaces(root, info, name=""):
    return [workspace for workspace in db.get_workspaces(name) if not name or workspace == name]

def query_graphs(root, info, workspace, name=""):
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace) if not name or graph == name]

def query_tables(root, info, workspace, name=""):
    return [Table(workspace, table) for table in db.workspace_tables(workspace) if not name or table == name]

def query_nodes(root, info, workspace, graph, nodeType=None, key=None, search=None):
    return EntityQuery(EntityType(Graph(workspace, graph), nodeType), key, search)

def query_edges(root, info, workspace, graph, edgeType=None, key=None, search=None):
    return EntityQuery(EntityType(Graph(workspace, graph), edgeType), key, search)

def query_rows(root, info, workspace, table, key=None, search=None):
    return RowQuery(Table(workspace, table), key, search)

def nodeCount(query, info):
    return db.countNodes(query)

def edgeCount(query, info):
    return db.countEdges(query)

def rowCount(query, info):
    logprint(query)
    return db.countRows(query)

def nodes(query, info, offset=0, limit=10):
    return db.fetchNodes(query, Cursor(offset, limit))

def edges(query, info, offset=0, limit=10):
    return db.fetchEdges(query, Cursor(offset, limit))

def rows(query, info, offset=0, limit=10):
    return db.fetchRows(query, Cursor(offset, limit))

def table_rows(table, info):
    return RowQuery(table, None, None)

def workspace_name(workspace, info):
    return workspace

def workspace_tables(workspace, info):
    return [Table(workspace, table) for table in db.workspace_tables(workspace)]

def workspace_graphs(workspace, info):
    return [Graph(workspace, graph) for graph in db.workspace_graphs(workspace)]

def graph_name(graph, info):
    return graph.name

def edgeTypes(graph, info):
    return db.graph_edge_types(graph)

def nodeTypes(graph, info):
    return db.graph_node_types(graph)

def graph_nodelist(graph, info):
    return EntityQuery(EntityType(graph, None), None, None)

def graph_edgelist(graph, info):
    return EntityQuery(EntityType(graph, None), None, None)

def table_name(table, info):
    return table.name

def table_fields(table, info):
    return db.table_fields(table)

def edgeSource(edge, info):
    return db.source(edge)

def edgeTarget(edge, info):
    return db.target(edge)

def nodeOutgoing(node, info):
    return db.outgoing(node)

def nodeIncoming(node, info):
    return db.incoming(node)

def attributes(data, info, keys=None):
    return [(key, value) for key, value in data.iteritems() if (keys is None) or (key in keys)]

# MUTATIONS
def create_workspace(root, info, name):
    db.create_workspace(name)
    return name

def create_graph(root, info, workspace, name, nodeTypes, edgeTypes):
    graph = Graph(workspace, name)
    # nodeTypes and edgeTypes are currently arrays of string table names, but will be converted
    db.create_graph(graph, nodeTypes, edgeTypes)
    return graph

def create_table(root, info, workspace, name, primaryKey='_id', fields=[]):
    table = Table(workspace, name)
    db.create_table(table)
    return table
