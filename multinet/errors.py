"""Exception objects representing Multinet-specific HTTP error conditions."""
from typing import Tuple, Any, Union, Dict, List, Sequence

from multinet.validation import ValidationFailure


FlaskTuple = Tuple[Any, Union[int, str]]


class ServerError(Exception):
    """Base exception for all HTTP errors in the Multinet server."""

    def flask_response(self) -> FlaskTuple:
        """
        Generate a value suitable for returning from a Flask view function.

        Typically this will be a tuple consisting of data describing the errors,
        and a status code. The code is typically a string consisting of the
        integer status code followed by a specific description of what that code
        means in the Multinet context.
        """

        raise NotImplementedError


class InternalServerError(ServerError):
    """General exception for internal server errors."""

    def __init__(self, message: str = ""):
        """Initialize the exception."""
        self.message = message

    def flask_response(self) -> FlaskTuple:
        """Generate a 500 level error."""
        return (self.message, "500 Internal Server Error")


class SecretKeyNotSet(InternalServerError):
    """Raised when app.secret_key has not been set."""

    def __init__(self) -> None:
        """Initialize parent class with message."""
        super().__init__("Flask secret key not set.")


class DatabaseCorrupted(ServerError):
    """The database has a consistency issue."""

    def flask_response(self) -> FlaskTuple:
        """Generate a 500 level error."""
        return ("", "500 Database Corrupted")


class Unauthorized(ServerError):
    """The request did not indicate sufficient permission."""

    def __init__(self, reason: str = ""):
        """Initialize the error with an optional reason."""
        self.reason = reason

    def flask_response(self) -> FlaskTuple:
        """Generate a 401 error."""
        return (self.reason, "401 Unauthorized")


class NotFound(ServerError):
    """Base exception for 404 errors of various types."""

    def __init__(self, item_type: str, item: str):
        """
        Initialize the instance with the type and identity of the missing item.

        `item_type` - the kind of item that is not found
        `item` - the name of the not found item
        """
        self.type = item_type
        self.item = item

    def flask_response(self) -> FlaskTuple:
        """Generate a 404 error for the missing item."""
        return (self.item, f"404 {self.type.capitalize()} Not Found")


class WorkspaceNotFound(NotFound):
    """Exception for missing workspace."""

    def __init__(self, workspace: str):
        """Initialize the exception."""
        super().__init__("Workspace", workspace)


class TableNotFound(NotFound):
    """Exception for missing table."""

    def __init__(self, workspace: str, table: str):
        """Initialize the exception."""
        super().__init__("Table", f"{workspace}/{table}")


class NetworkNotFound(NotFound):
    """Exception for missing network."""

    def __init__(self, workspace: str, graph: str):
        """Initialize the exception."""
        super().__init__("Network", f"{workspace}/{graph}")


class NodeNotFound(NotFound):
    """Exception for missing node."""

    def __init__(self, table: str, node: str):
        """Initialize the exception."""
        super().__init__("Node", f"{table}/{node}")


class BadQueryArgument(ServerError):
    """Exception for illegal query argument value."""

    def __init__(self, argument: str, value: str):
        """Initialize the exception."""
        self.argument = argument
        self.value = value

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error for the bad argument."""
        payload = {"argument": self.argument, "value": self.value}
        return (payload, "400 Bad Query Argument")


class AlreadyExists(ServerError):
    """Exception for attempting to create a resource that already exists."""

    def __init__(self, item_type: str, item: str):
        """Initialize the exception."""
        self.type = item_type
        self.item = item

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error for the bad argument."""
        return (self.item, f"409 {self.type.capitalize()} Already Exists")


class MalformedRequestBody(ServerError):
    """Exception for passing an unreadable request body."""

    def __init__(self, body: str):
        """Initialize the exception."""
        self.body = body

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.body, "400 Malformed Request Body")


class InvalidMetadata(ServerError):
    """Exception for specifying invalid metadata."""

    def __init__(self, metadata: Dict):
        """Initialize the exception."""
        self.metadata = metadata

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.metadata, "400 Invalid Metadata")


class RequiredParamsMissing(ServerError):
    """Exception for missing required parameters."""

    def __init__(self, missing: List[str]):
        """Initialize the exception."""
        self.missing = {"missing": missing}

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.missing, "400 Required Parameters Missing")


class InvalidName(ServerError):
    """Exception for invalid resource name."""

    def __init__(self, name: str):
        """Initialize the exception."""
        self.name = name

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error for the bad argument."""
        return (self.name, "400 Invalid Name")


class ValidationFailed(ServerError):
    """Exception for reporting validation errors."""

    def __init__(self, errors: Sequence[ValidationFailure]):
        """Initialize the exception."""
        self.errors = [error.dict() for error in errors]

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return ({"errors": self.errors}, "400 Validation Failed")


class DatabaseNotLive(ServerError):
    """Exception for when Arango database is not live."""

    def flask_response(self) -> FlaskTuple:
        """Generate a 500 error."""
        return ("", "500 Database Not Live")


class DecodeFailed(ServerError):
    """Exception for reporting decoding errors."""

    def __init__(self, error: str):
        """Initialize the exception."""
        self.error = error

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.error, "400 Decode Failed")


class GraphCreationError(ServerError):
    """Exception for errors when creating a graph in Arango."""

    def __init__(self, message: str):
        """Initialize error message."""
        self.message = message

    def flask_response(self) -> FlaskTuple:
        """Generate a 500 error."""
        return (self.message, "500 Graph Creation Failed")


class AQLValidationError(ServerError):
    """Exception for errors when validating an aql query in Arango."""

    def __init__(self, message: str = ""):
        """Initialize error message."""
        self.message = message

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.message, "400 AQL Validation Failed")


class AQLExecutionError(ServerError):
    """Exception for errors when executing an aql query in Arango."""

    def __init__(self, message: str = ""):
        """Initialize error message."""
        self.message = message

    def flask_response(self) -> FlaskTuple:
        """Generate a 400 error."""
        return (self.message, "400 Error during AQL Execution")


class UploadNotFound(NotFound):
    """Exception for attempting to upload a chunk to a nonexistant upload collection."""

    def __init__(self, upload_id: str):
        """Initialize the exception."""
        super().__init__("Upload", upload_id)
