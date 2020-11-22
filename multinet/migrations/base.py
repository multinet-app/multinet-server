"""Base classes that other migrations inherit from."""


class Migration:
    """
    The parent class to which all migrations should inherit from.

    This class must implement a single method, `run`. This method is the entry point
    for the migration. Any necessary helper methods or variables can be added to the
    migration class itself. All methods/variables in these classes should be static,
    and none of these classes should be instantiated.
    """

    @staticmethod
    def run() -> None:
        """All subclasses should override this method."""
        raise NotImplementedError
