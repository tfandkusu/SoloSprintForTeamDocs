"""Document manager abstractions."""

from typing import Protocol, runtime_checkable

from ss4d.model.task import Task


@runtime_checkable
class DocumentManager(Protocol):
    """Abstract document manager used by task processes."""

    def append_task(self, number: int, title: str) -> None:
        """Append a task to the configured document."""
        ...

    def read_tasks(self) -> list[Task]:
        """Read all tasks from the configured document."""
        ...

    def write_tasks(self, tasks: list[Task]) -> None:
        """Overwrite the configured document with the supplied tasks."""
        ...

    def sort_tasks(self) -> None:
        """Sort task sections in the configured document."""
        ...

    def update_task_status(self, number: int, status: str) -> None:
        """Update a task status in the configured document."""
        ...

    def update_task_due_date(self, number: int, due_date: str) -> None:
        """Update a task due date in the configured document."""
        ...
