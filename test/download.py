from pprint import pprint
import sys

from common import WORKSPACE, graph_nodes


if __name__ == '__main__':
    # Dump the nodes from the graph.
    nodes = graph_nodes(WORKSPACE, 'boston')
    pprint(nodes.json())

    # Dump just the member nodes.
    nodes = graph_nodes(WORKSPACE, 'boston', node_type='members')
    pprint(nodes.json())

    # And just the club nodes.
    nodes = graph_nodes(WORKSPACE, 'boston', node_type='clubs')
    pprint(nodes.json())

    # Find a specific node.
    nodes = graph_nodes(WORKSPACE, 'boston', key='clubs/0')
    pprint(nodes.json())
