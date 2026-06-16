"""Document manager abstractions."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentManager(Protocol):
    """Abstract document manager used by task processes."""

    def append_task(self, number: int, title: str) -> None:
        """Append a task to the configured document."""
        ...

    def sort_tasks(self) -> None:
        """Sort task sections in the configured document."""
        ...

    def update_task_status(self, number: int, status: str) -> None:
        """Update a task status in the configured document."""
        ...
