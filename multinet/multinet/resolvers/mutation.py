from multinet import db
from multinet.types import Graph, Table, EntityType


def workspace(root, info, name):
    db.create_workspace(name)
    return name


def delete_workspace(root, info, name):
    return name if db.delete_workspace(name) else None


def graph(root, info, workspace, name):
    graph = Graph(workspace, name)
    db.create_graph(graph)
    return graph


def table(root, info, workspace, name, edges=False, primaryKey='_id', fields=[]):
    table = Table(workspace, name)
    db.create_table(table, edges)
    return table


def entity_type(root, info, workspace, graph, table, properties):
    entity_type = EntityType(workspace, graph, table)
    db.create_type(entity_type, properties)
    return entity_type


def add_resolvers(schema):
    fields = schema.get_type('Mutation').fields
    fields['workspace'].resolver = workspace
    fields['deleteWorkspace'].resolver = delete_workspace
    fields['graph'].resolver = graph
    fields['table'].resolver = table
    fields['entityType'].resolver = entity_type
