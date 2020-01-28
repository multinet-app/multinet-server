"""Multinet uploader for Newick tree files."""
from flasgger import swag_from
import uuid
import newick

from .. import db, util
from ..errors import ValidationFailed
from ..util import decode_data

from flask import Blueprint, request
from flask import current_app as app

from typing import Any, Optional, List, Dict, Set, FrozenSet, Tuple

bp = Blueprint("newick", __name__)
bp.before_request(util.require_db)


def validate_newick(tree: List[newick.Node]) -> None:
    """Validate newick tree."""
    data_errors: List[Dict[str, Any]] = []
    unique_keys: Set[str] = set()
    duplicate_keys: Set[str] = set()
    unique_edges: Set[FrozenSet[Tuple[str, object]]] = set()
    duplicate_edges: Set[FrozenSet[Tuple[str, object]]] = set()

    def read_tree(parent: Optional[str], node: newick.Node) -> None:
        key = node.name or uuid.uuid4().hex

        if key in unique_keys:
            duplicate_keys.add(key)
        else:
            unique_keys.add(key)

        for desc in node.descendants:
            read_tree(key, desc)

        if parent:
            edge = frozenset(
                {
                    "_from": f"table/{parent}",
                    "_to": f"table/{key}",
                    "length": node.length,
                }.items()
            )

            if edge in unique_edges:
                duplicate_edges.add(edge)
            else:
                unique_edges.add(edge)

    read_tree(None, tree[0])

    if len(duplicate_keys) > 0:
        data_errors.append({"error": "duplicate", "detail": list(duplicate_keys)})

    if len(duplicate_edges) > 0:
        data_errors.append(
            {"error": "duplicate", "detail": [dict(x) for x in duplicate_edges]}
        )

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)
    else:
        return


@bp.route("/<workspace>/<table>", methods=["POST"])
@swag_from("swagger/newick.yaml")
def upload(workspace: str, table: str) -> Any:
    """
    Store a newick tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `table` - the target table.
    `data` - the newick data, passed in the request body.
    """
    app.logger.info("newick tree")

    body = decode_data(request.data)

    tree = newick.loads(body)

    validate_newick(tree)

    space = db.db(workspace)
    edgetable_name = "%s_edges" % table
    nodetable_name = "%s_nodes" % table
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

    return {"edgecount": edgecount, "nodecount": nodecount}
