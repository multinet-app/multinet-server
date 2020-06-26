"""Multinet uploader for Newick tree files."""
from flasgger import swag_from
import uuid
import newick

from multinet import db, util
from multinet.auth.util import require_writer
from multinet.errors import ValidationFailed, AlreadyExists
from multinet.util import decode_data
from multinet.validation import ValidationFailure, DuplicateKey

from dataclasses import dataclass
from flask import Blueprint, request
from flask import current_app as app

from typing import Any, Optional, List, Set, Tuple

bp = Blueprint("newick", __name__)
bp.before_request(util.require_db)


@dataclass
class DuplicateEdge(ValidationFailure):
    """The edge which is duplicated."""

    _from: str
    _to: str
    length: int


def validate_newick(tree: List[newick.Node]) -> None:
    """Validate newick tree."""
    data_errors: List[ValidationFailure] = []
    unique_keys: Set[str] = set()
    unique_edges: Set[Tuple[str, str, float]] = set()

    def read_tree(parent: Optional[str], node: newick.Node) -> None:
        key = node.name or uuid.uuid4().hex

        if key in unique_keys:
            data_errors.append(DuplicateKey(key=key))
        else:
            unique_keys.add(key)

        for desc in node.descendants:
            read_tree(key, desc)

        if parent:
            unique = (parent, key, node.length)
            if unique in unique_edges:
                data_errors.append(
                    DuplicateEdge(
                        _from=f"table/{parent}", _to=f"table/{key}", length=node.length
                    )
                )
            else:
                unique_edges.add(unique)

    read_tree(None, tree[0])

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)


@bp.route("/<workspace>/<graph>", methods=["POST"])
@require_writer
@swag_from("swagger/newick.yaml")
def upload(workspace: str, graph: str) -> Any:
    """
    Store a newick tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `graph` - the target graph.
    `data` - the newick data, passed in the request body.
    """
    app.logger.info("newick tree")

    body = decode_data(request.data)

    tree = newick.loads(body)

    validate_newick(tree)

    space = db.get_workspace_db(workspace)
    if space.has_graph(graph):
        raise AlreadyExists("graph", graph)

    edgetable_name = f"{graph}_edges"
    nodetable_name = f"{graph}_nodes"

    if space.has_collection(edgetable_name):
        edgetable = space.collection(edgetable_name)
    else:
        # Note that edge=True must be set or the _from and _to keys
        # will be ignored below.
        edgetable = space.create_collection(edgetable_name, edge=True)

    if space.has_collection(nodetable_name):
        nodetable = space.collection(nodetable_name)
    else:
        nodetable = space.create_collection(nodetable_name)

    edgecount = 0
    nodecount = 0

    def read_tree(parent: Optional[str], node: newick.Node) -> None:
        nonlocal nodecount
        nonlocal edgecount
        key = node.name or uuid.uuid4().hex
        if not nodetable.has(key):
            nodetable.insert({"_key": key})
        nodecount = nodecount + 1
        for desc in node.descendants:
            read_tree(key, desc)
        if parent:
            edgetable.insert(
                {
                    "_from": "%s/%s" % (nodetable_name, parent),
                    "_to": "%s/%s" % (nodetable_name, key),
                    "length": node.length,
                }
            )
            edgecount += 1

    read_tree(None, tree[0])
    edge_table_info = util.get_edge_table_properties(workspace, edgetable_name)
    db.create_graph(
        workspace,
        graph,
        edgetable_name,
        edge_table_info["from_tables"],
        edge_table_info["to_tables"],
    )

    return {"edgecount": edgecount, "nodecount": nodecount}
