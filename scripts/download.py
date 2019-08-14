from pprint import pprint

from common import WORKSPACE, graph_nodes, graph_edges, table_rows


if __name__ == "__main__":
    # Dump the nodes from the graph.
    nodes = graph_nodes(WORKSPACE, "boston")
    pprint(nodes.json())

    # Dump just the member nodes.
    nodes = graph_nodes(WORKSPACE, "boston", node_type="members")
    pprint(nodes.json())

    # And just the club nodes.
    nodes = graph_nodes(WORKSPACE, "boston", node_type="clubs")
    pprint(nodes.json())

    # Find a specific node.
    nodes = graph_nodes(WORKSPACE, "boston", key="clubs/0")
    pprint(nodes.json())

    # Get all the edges.
    edges = graph_edges(WORKSPACE, "boston")
    pprint(edges.json())

    # Get a specific edge.
    edges = graph_edges(WORKSPACE, "boston", key="membership/9701679")
    pprint(edges.json())

    # Dump rows from a table.
    rows = table_rows(WORKSPACE, "members")
    pprint(rows.json())

    # Dump a specific row from a table.
    rows = table_rows(WORKSPACE, "members", key="members/142")
    pprint(rows.json())
