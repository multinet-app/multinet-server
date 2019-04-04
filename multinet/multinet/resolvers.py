import os
import logging
from girder import plugin, logprint

from . import db

def allNodes(root, info, graph, type, id):
  dbgraph = db.graph(graph)
  collections = []
  if type:
      collections.append(dbgraph.vertex_collection(type))
  else:
      collections = [dbgraph.vertex_collection(coll) for coll in dbgraph.vertex_collections()]

  vertices = []
  if id:
      vertices = [(dbgraph, coll.get(id)) for coll in collections if coll.get(id)]
  else:
      vertices = [(dbgraph, vert) for coll in collections for vert in coll.all()]
  return vertices

def allEdges(root, info, graph, type, id):
  dbgraph = db.graph(graph)
  collections = []
  if type:
      collections.append(type)
  else:
      collections = [coll for coll in dbgraph.edge_collections()]

  edges = []
  if id:
      edges = [(dbgraph, coll.get(id)) for coll in collections if coll.get(id)]
  else:
      edges = [(dbgraph, edge) for coll in collections for edge in coll.all()]

  return edges

def edgeSource(edge, info):
    return (edge[0], edge[0].vertex(edge[1]['_from']))

def edgeTarget(edge, info):
    return (edge[0], edge[0].vertex(edge[1]['_to']))

def nodeOutgoing(node, info):
    graph = node[0]
    edgeColls = [graph.edge_collection(edge_def['edge_collection']) for edge_def in graph.edge_definitions()]
    edges = [(node[0], edge) for edgeColl in edgeColls for edge in edgeColl.edges(node[1]['_id'], direction='out')['edges']]
    return edges

def nodeIncoming(node, info):
    graph = node[0]
    edgeColls = [graph.edge_collection(edge_def['edge_collection']) for edge_def in graph.edge_definitions()]
    edges = [(node[0], edge) for edgeColl in edgeColls for edge in edgeColl.edges(node[1]['_id'], direction='in')['edges']]
    return edges

def attributes(document, info, source, keys):
    return [(key, value) for key, value in document[1].iteritems() if key in keys]

def create_workspace(root, info, name):
    db.create_workspace(name)
    return name

def create_graph(root, info, workspace, name, nodeTables, edgeTables):
    db.create_graph(workspace, name, nodeTables, edgeTables)
    return name
