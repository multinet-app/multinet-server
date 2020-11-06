"""Multinet uploader for Newick tree files."""
from flasgger import swag_from
import uuid
import newick

from multinet import util
from multinet.db.models.workspace import Workspace
from multinet.auth.util import require_writer
from multinet.errors import ValidationFailed, AlreadyExists
from multinet.util import decode_data
from multinet.validation import ValidationFailure, DuplicateKey

from flask import Blueprint, request
from flask import current_app as app

from typing import Any, Optional, List, Set, Tuple

bp = Blueprint("newick", __name__)
bp.before_request(util.require_db)


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

    loaded_workspace = Workspace(workspace)
    if loaded_workspace.has_graph(graph):
        raise AlreadyExists("graph", graph)

    body = decode_data(request.data)
    tree = newick.loads(body)
    validate_newick(tree)

    edgetable_name = f"{graph}_edges"
    nodetable_name = f"{graph}_nodes"

    if loaded_workspace.has_table(edgetable_name):
        edgetable = loaded_workspace.table(edgetable_name)
    else:
        # Note that edge=True must be set or the _from and _to keys
        # will be ignored below.
        edgetable = loaded_workspace.create_table(edgetable_name, edge=True)

    if loaded_workspace.has_table(nodetable_name):
        nodetable = loaded_workspace.table(nodetable_name)
    else:
        nodetable = loaded_workspace.create_table(nodetable_name, edge=False)

    edgecount = 0
    nodecount = 0

    def read_tree(parent: Optional[str], node: newick.Node) -> None:
        nonlocal nodecount
        nonlocal edgecount
        key = node.name or uuid.uuid4().hex
        if not nodetable.row(key):
            nodetable.insert([{"_key": key}])
        nodecount = nodecount + 1
        for desc in node.descendants:
            read_tree(key, desc)
        if parent:
            edgetable.insert(
                [
                    {
                        "_from": f"{nodetable_name}/{parent}",
                        "_to": f"{nodetable_name}/{key}",
                        "length": node.length,
                    }
                ]
            )
            edgecount += 1

    read_tree(None, tree[0])

    loaded_workspace.create_graph(graph, edgetable_name)

    return {"edgecount": edgecount, "nodecount": nodecount}
