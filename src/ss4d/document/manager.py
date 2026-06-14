"""Document manager abstractions."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentManager(Protocol):
    """Abstract document manager used by task processes."""

    def append_task(self, number: int, title: str) -> None:
        """Append a task to the configured document."""
        ...
