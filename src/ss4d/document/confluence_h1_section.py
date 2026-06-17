"""Confluence h1 section value object."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class H1Section:
    """An h1-led section from a Confluence HTML body."""

    body: str
    due_date: date | None
    is_done: bool
    number: int | None
