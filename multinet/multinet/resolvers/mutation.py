from multinet import db
from multinet.types import Graph, Table


def workspace(root, info, name):
    db.create_workspace(name)
    return name


def graph(root, info, workspace, name, nodeTypes, edgeTypes):
    graph = Graph(workspace, name)
    # nodeTypes and edgeTypes are currently arrays of string table names, but will be converted
    db.create_graph(graph, nodeTypes, edgeTypes)
    return graph


def table(root, info, workspace, name, edges=False, primaryKey='_id', fields=[]):
    table = Table(workspace, name)
    db.create_table(table, edges)
    return table


def add_resolvers(schema):
    fields = schema.get_type('Mutation').fields
    fields['workspace'].resolver = workspace
    fields['graph'].resolver = graph
    fields['table'].resolver = table
