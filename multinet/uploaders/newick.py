"""Multinet uploader for Newick tree files."""
import uuid
import newick

from .. import db, multinet

from flask import Blueprint, request
from flask import current_app as app

bp = Blueprint("newick", __name__)
bp.before_request(multinet.require_db)


@bp.route("/<workspace>/<table>", methods=["POST"])
def upload(workspace, table):
    """
    Store a newick tree into the database in coordinated node and edge tables.

    `workspace` - the target workspace.
    `table` - the target table.
    `data` - the newick data, passed in the request body.
    """
    app.logger.info("newick tree")
    tree = newick.loads(request.data.decode("utf8"))
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
