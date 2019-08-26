"""Multinet uploader for Newick tree files."""
import uuid
import newick

from .. import db, api

from flask import Blueprint, request
from flask import current_app as app

bp = Blueprint("newick", __name__)
bp.before_request(api.require_db)


def validate_newick(tree):
    """Validate newick tree."""
    data_errors = []
    unique_keys = []
    duplicate_keys = []
    unique_edges = []
    duplicate_edges = []

    def read_tree(parent, node):
        nonlocal data_errors
        nonlocal unique_keys
        nonlocal duplicate_keys
        nonlocal unique_edges
        nonlocal duplicate_edges

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
        return data_errors
    else:
        return


def decode_data(input):
    """Decode the request data assuming utf8 encoding."""
    try:
        body = input.decode("utf8")
    except UnicodeDecodeError:
        return None

    return body


@bp.route("/<workspace>/<table>", methods=["POST"])
def upload(workspace, table):
    """
    Store a newick tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `table` - the target table.
    `data` - the newick data, passed in the request body.
    """
    app.logger.info("newick tree")

    body = decode_data(request.data)
    if not body:
        response = {"errors": [{"error": "unsupported", "detail": "not utf8"}]}
        return (response, "400 Newick Decode Failed")

    tree = newick.loads(body)

    result = validate_newick(tree)
    if result:
        return ({"errors": result}, "400 Newick Validation Failed")

    workspace = db.db(workspace)
    edgetable_name = "%s_edges" % table
    nodetable_name = "%s_nodes" % table
    if workspace.has_collection(edgetable_name):
        edgetable = workspace.collection(edgetable_name)
    else:
        # Note that edge=True must be set or the _from and _to keys
        # will be ignored below.
        edgetable = workspace.create_collection(edgetable_name, edge=True)
    if workspace.has_collection(nodetable_name):
        nodetable = workspace.collection(nodetable_name)
    else:
        nodetable = workspace.create_collection(nodetable_name)

    edgecount = 0
    nodecount = 0

    def read_tree(parent, node):
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
