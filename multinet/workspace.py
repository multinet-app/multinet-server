"""Operations that deal with workspaces."""
from __future__ import annotations  # noqa: T484

import copy
import dataclasses
from dataclasses import dataclass
from arango.exceptions import DatabaseCreateError, EdgeDefinitionCreateError
from arango.cursor import Cursor

from multinet import util
from multinet.types import EdgeTableProperties
from multinet.validation import ValidationFailure, UndefinedTable, UndefinedKeys
from multinet.validation.csv import validate_csv
from multinet.db import (
    workspace_mapping,
    workspace_mapping_collection,
    db,
    system_db,
    _run_aql_query,
)
from multinet.errors import (
    AlreadyExists,
    ValidationFailed,
    InternalServerError,
    WorkspaceNotFound,
    BadQueryArgument,
    GraphNotFound,
    TableNotFound,
    GraphCreationError,
)
from multinet.user import User
from multinet.graph import Graph
from multinet.table import Table

from typing import Any, List, Dict, Generator, Optional


@dataclass
class WorkspacePermissions:
    """The permissions on a workspace."""

    # TODO: Change str to User once updating permissions storage
    # https://github.com/multinet-app/multinet-server/issues/456
    owner: str
    maintainers: List[str] = dataclasses.field(default_factory=lambda: [])
    writers: List[str] = dataclasses.field(default_factory=lambda: [])
    readers: List[str] = dataclasses.field(default_factory=lambda: [])
    public: bool = False


class Workspace:
    """Workspaces contain Multinet Tables and Graphs."""

    # Keys that aren't saved to the database
    exclude_keys = {"handle", "readonly_handle", "readonly"}

    def __init__(self, name: str):
        """
        Intialize a Workspace.

        Retrieve the workspace metadata and populate this object. If the workspace
        does not exist, this construction raises a `WorkspaceNotFound` error.
        """
        self.name = name

        # TODO: Don't access database right away
        doc = self.get_metadata()

        # Due to call above, doc is guaranteed to be valid
        self.internal: str = doc["internal"]
        self.permissions: WorkspacePermissions = WorkspacePermissions(
            **doc["permissions"]
        )

        self.readonly_handle = db(self.internal)
        self.handle = db(self.internal, readonly=False)

    @staticmethod
    def exists(name: str) -> bool:
        """Return if this workspace exists or not."""
        return bool(workspace_mapping(name))

    @staticmethod
    def create(name: str, owner: User) -> Workspace:
        """Create a workspace, owned by `owner`."""
        if Workspace.exists(name):
            raise AlreadyExists("Workspace", name)

        internal = util.generate_arango_workspace_name()

        try:
            system_db(readonly=False).create_database(internal)
        except DatabaseCreateError:
            # Could only happen if there's a name collision
            raise InternalServerError("Error creating workspace")

        permissions = WorkspacePermissions(owner=owner.sub).__dict__
        workspace_dict = {
            "name": name,
            "internal": internal,
            "permissions": permissions,
        }

        coll = workspace_mapping_collection(readonly=False)
        coll.insert(workspace_dict, sync=True)
        workspace_mapping.cache_clear()

        return Workspace(name)

    @staticmethod
    def list_all() -> Generator[str, None, None]:
        """Return a list of all workspace names."""
        coll = workspace_mapping_collection()
        return (doc["name"] for doc in coll.all())

    @staticmethod
    def list_public() -> Generator[str, None, None]:
        """Return a list of all public workspace names."""
        coll = workspace_mapping_collection()
        return (doc["name"] for doc in coll.find({"permissions.public": True}))

    @staticmethod
    def from_dict(d: Dict) -> Workspace:
        """Construct a workspace from a dict."""
        workspace = Workspace(name=d["name"])

        return workspace

    def save(self) -> None:
        """Save this workspace to the database."""
        doc = self.get_metadata()
        instance_dict = self.asdict()

        doc.update(instance_dict)

        coll = workspace_mapping_collection(readonly=False)
        coll.update(doc)

        # Invalidate the cache for things changed by this function
        workspace_mapping.cache_clear()

    def get_permissions(self) -> WorkspacePermissions:
        """Fetch and return the permissions on this workspace."""
        doc = self.get_metadata()

        self.permissions = self.permissions or doc["permissions"]
        self.internal = self.internal or doc["internal"]

        return WorkspacePermissions(**doc["permissions"])

    def set_permissions(
        self, permissions: WorkspacePermissions
    ) -> WorkspacePermissions:
        """Set the permissions on a workspace."""
        # Disallow changing workspace ownership through this function.
        current_owner = self.permissions.owner
        self.permissions = permissions
        self.permissions.owner = current_owner

        self.save()
        return self.permissions

    def asdict(self) -> Dict:
        """Return this workspace as a dictionary."""
        filtered = {
            k: v for k, v in self.__dict__.items() if k not in Workspace.exclude_keys
        }
        filtered["permissions"] = self.permissions.__dict__

        return filtered

    def rename(self, new_name: str) -> None:
        """Rename this workspace."""
        if Workspace.exists(new_name):
            raise AlreadyExists("Workspace", new_name)

        doc = self.get_metadata()
        doc["name"] = new_name

        coll = workspace_mapping_collection(readonly=False)
        coll.update(doc)

        self.name = new_name

        # Invalidate the cache for things changed by this function
        workspace_mapping.cache_clear()

    def delete(self) -> None:
        """Delete this workspace."""
        doc = self.get_metadata()

        sysdb = system_db(readonly=False)
        coll = workspace_mapping_collection(readonly=False)

        sysdb.delete_database(doc["internal"])
        coll.delete(doc["_id"])

        # Invalidate the cache for things changed by this function
        workspace_mapping.cache_clear()

    def get_metadata(self) -> Dict:
        """Fetch and return the metadata for this workspace."""
        doc = workspace_mapping(self.name)
        if not doc:
            raise WorkspaceNotFound(self.name)

        # Copy so modifications to return don't poison cache
        return copy.deepcopy(doc)

    # Graphs
    def graphs(self) -> List[Dict]:
        """Return the graphs in this workspace."""
        return self.readonly_handle.graphs()

    def graph(self, name: str) -> Graph:
        """Return a specific graph."""
        if not self.readonly_handle.has_graph(name):
            raise GraphNotFound(self.name, name)

        return Graph(name, self.name, self.handle.graph(name), self.handle.aql)

    def has_graph(self, name: str) -> bool:
        """Return if a specific graph exists."""
        return self.readonly_handle.has_graph(name)

    def validate_edge_table(self, edge_table: str) -> EdgeTableProperties:
        """
        Validate that an edge table is suitable for use in a graph.

        If validation is successful, the edge table properties are returned.
        Otherwise, a ValidationFailed error is raised.
        """
        loaded_edge_table = self.table(edge_table)
        edge_table_properties = loaded_edge_table.edge_properties()

        referenced_tables = edge_table_properties["table_keys"]

        errors: List[ValidationFailure] = []
        for table, keys in referenced_tables.items():
            if not self.has_table(table):
                errors.append(UndefinedTable(table=table))
            else:
                table_keys = set(self.table(table).keys())
                undefined = keys - table_keys

                if undefined:
                    errors.append(UndefinedKeys(table=table, keys=list(undefined)))

        if errors:
            raise ValidationFailed(errors)

        return edge_table_properties

    def create_graph(self, name: str, edge_table: str) -> None:
        """Create a graph."""
        if self.has_graph(name):
            raise AlreadyExists("Graph", name)

        edge_table_properties = self.validate_edge_table(edge_table)
        from_tables = edge_table_properties["from_tables"]
        to_tables = edge_table_properties["to_tables"]

        try:
            self.handle.create_graph(
                name,
                edge_definitions=[
                    {
                        "edge_collection": edge_table,
                        "from_vertex_collections": list(from_tables),
                        "to_vertex_collections": list(to_tables),
                    }
                ],
            )
        except EdgeDefinitionCreateError as e:
            raise GraphCreationError(str(e))

    def delete_graph(self, name: str) -> bool:
        """Delete a specific graph."""
        if not self.has_graph(name):
            raise GraphNotFound(self.name, name)

        return self.handle.delete_graph(name)

    # Tables
    def tables(self, table_type: str = "all") -> Generator[str, None, None]:
        """Return all tables of the specified type."""

        def pass_all(x: Dict[str, Any]) -> bool:
            return True

        def is_edge(x: Dict[str, Any]) -> bool:
            return x["edge"]

        def is_node(x: Dict[str, Any]) -> bool:
            return not x["edge"]

        if table_type == "all":
            desired_type = pass_all
        elif table_type == "node":
            desired_type = is_node
        elif table_type == "edge":
            desired_type = is_edge
        else:
            raise BadQueryArgument("type", table_type, ["all", "node", "edge"])

        tables = (
            table["name"]
            for table in self.readonly_handle.collections()
            if not table["system"]
            and desired_type(
                self.readonly_handle.collection(table["name"]).properties()
            )
        )

        return tables

    def table(self, name: str) -> Table:
        """Return a specific table."""
        return Table(name, self.name, self.handle.collection(name), self.handle.aql)

    def has_table(self, name: str) -> bool:
        """Return if a specific table exists."""
        return self.readonly_handle.has_collection(name)

    def create_table(self, table: str, edge: bool, sync: bool = False) -> Table:
        """Create a table in this workspace."""
        table_handle = self.handle.create_collection(table, edge=edge, sync=sync)
        return Table(table, self.name, table_handle, self.handle.aql)

    def create_aql_table(self, table: str, aql_query: str) -> Table:
        """Create a table in this workspace from an aql query."""
        if self.has_table(table):
            raise AlreadyExists("table", table)

        # In the future, the result of this validation can be
        # used to determine dependencies in virtual tables
        rows = list(self.run_query(aql_query))
        validate_csv(rows, "_key", False)

        loaded_table = self.create_table(table, False)
        loaded_table.insert(rows)

        return loaded_table

    def delete_table(self, table: str) -> None:
        """Delete a specific table."""
        if not self.has_table(table):
            raise TableNotFound(self.name, table)

        self.handle.delete_collection(table)

    def run_query(self, query: str, bind_vars: Optional[Dict] = None) -> Cursor:
        """Run an aql query on this workspace."""
        return _run_aql_query(self.readonly_handle.aql, query, bind_vars=bind_vars)
