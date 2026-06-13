"""Document manager abstractions."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class DocumentManager(Protocol):
    """Abstract document manager used by task processes."""

    def append_heading(self, heading: str) -> None:
        """Append a heading to the configured document."""
        ...
