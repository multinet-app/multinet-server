"""Exception objects representing Multinet-specific HTTP error conditions."""


class ServerError(Exception):
    """Base exception for all HTTP errors in the Multinet server."""

    def flask_response(self):
        """
        Generate a value suitable for returning from a Flask view function.

        Typically this will be a tuple consisting of data describing the errors,
        and a status code. The code is typically a string consisting of the
        integer status code followed by a specific description of what that code
        means in the Multinet context.
        """

        raise NotImplementedError


class NotFound(ServerError):
    """Base exception for 404 errors of various types."""

    def __init__(self, type, item):
        """
        Initialize the instance with the type and identity of the missing item.

        `type` - the kind of item that is not found
        `item` - the name of the not found item
        """
        self.type = type
        self.item = item

    def flask_response(self):
        """Generate a 404 error for the missing item."""
        return (self.item, f"404 {self.type.capitalize()} Not Found")


class WorkspaceNotFound(NotFound):
    """Exception for missing workspace."""

    def __init__(self, workspace):
        """Initialize the exception."""
        super().__init__("Workspace", workspace)


class TableNotFound(NotFound):
    """Exception for missing table."""

    def __init__(self, workspace, table):
        """Initialize the exception."""
        super().__init__("Table", f"{workspace}/{table}")


class GraphNotFound(NotFound):
    """Exception for missing graph."""

    def __init__(self, workspace, graph):
        """Initialize the exception."""
        super().__init__("Graph", f"{workspace}/{graph}")


class NodeNotFound(NotFound):
    """Exception for missing node."""

    def __init__(self, table, node):
        """Initialize the exception."""
        super().__init__("Node", f"{table}/{node}")


class BadQueryArgument(ServerError):
    """Exception for illegal query argument value."""

    def __init__(self, argument, value, allowed=None):
        """Initialize the exception."""
        self.argument = argument
        self.value = value
        self.allowed = allowed or []

    def flask_response(self):
        """Generate a 400 error for the bad argument."""
        payload = {"argument": self.argument, "value": self.value}

        if self.allowed:
            payload["allowed"] = self.allowed

        return (payload, "400 Bad Query Argument")


class AlreadyExists(ServerError):
    """Exception for attempting to create a resource that already exists."""

    def __init__(self, type, item):
        """Initialize the exception."""
        self.type = type
        self.item = item

    def flask_response(self):
        """Generate a 400 error for the bad argument."""
        return (self.item, f"409 {self.type.capitalize()} Already Exists")


class InvalidName(ServerError):
    """Exception for invalid resource name."""

    def __init__(self, name):
        """Initialize the exception."""
        self.name = name

    def flask_response(self):
        """Generate a 400 error for the bad argument."""
        return (self.name, "400 Invalid Name")


class ValidationFailed(ServerError):
    """Exception for reporting validation errors."""

    def __init__(self, errors):
        """Initialize the exception."""
        self.errors = errors

    def flask_response(self):
        """Generate a 400 error."""
        return ({"errors": self.errors}, "400 Validation Failed")


class DatabaseNotLive(ServerError):
    """Exception for when Arango database is not live."""

    def flask_response(self):
        """Generate a 500 error."""
        return ("", "500 Database Not Live")
