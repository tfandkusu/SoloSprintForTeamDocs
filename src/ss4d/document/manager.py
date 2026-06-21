"""Document manager abstractions."""

from typing import Protocol, runtime_checkable

from ss4d.model.task import Task


@runtime_checkable
class DocumentManager(Protocol):
    """Abstract document manager used by task processes."""

    def read_tasks(self) -> list[Task]:
        """Read all tasks from the configured document."""
        ...

    def write_tasks(self, tasks: list[Task]) -> None:
        """Overwrite the configured document with the supplied tasks."""
        ...
