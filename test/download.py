from pprint import pprint
import sys

from common import WORKSPACE, graph_nodes


if __name__ == '__main__':
    # Dump the nodes from the graph.
    nodes = graph_nodes(WORKSPACE, 'boston')
    pprint(nodes.json())
