"""Multinet uploader for Newick tree files."""
import uuid
import newick

from .. import db, util
from ..errors import ValidationFailed
from ..util import decode_data

from flask import Blueprint, request
from flask import current_app as app

from typing import Any, Optional, List, Dict

bp = Blueprint("newick", __name__)
bp.before_request(util.require_db)


def validate_newick(tree: List[newick.Node]) -> None:
    """Validate newick tree."""
    data_errors: List[Dict[str, Any]] = []
    unique_keys: List[str] = []
    duplicate_keys: List[str] = []
    unique_edges: List[dict] = []
    duplicate_edges: List[dict] = []

    def read_tree(parent: Optional[str], node: newick.Node) -> None:
        key = node.name or uuid.uuid4().hex

        if key not in unique_keys:
            unique_keys.append(key)
        elif key not in duplicate_keys:
            duplicate_keys.append(key)

        for desc in node.descendants:
            read_tree(key, desc)

        if parent:
            edge = {
                "_from": "table/%s" % (parent),
                "_to": "table/%s" % (key),
                "length": node.length,
            }

            if edge not in unique_edges:
                unique_edges.append(edge)
            elif edge not in duplicate_edges:
                duplicate_edges.append(edge)

    read_tree(None, tree[0])

    if len(duplicate_keys) > 0:
        data_errors.append({"error": "duplicate", "detail": duplicate_keys})

    if len(duplicate_edges) > 0:
        data_errors.append({"error": "duplicate", "detail": duplicate_edges})

    if len(data_errors) > 0:
        raise ValidationFailed(data_errors)
    else:
        return


@bp.route("/<workspace>/<table>", methods=["POST"])
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

    return dict(edgecount=edgecount, nodecount=nodecount)
