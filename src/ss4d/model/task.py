"""Task domain model."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TaskStatus(StrEnum):
    """Supported workflow statuses for a task."""

    TODO = "todo"
    PROGRESS = "progress"
    REVIEW = "review"
    DONE = "done"


@dataclass(frozen=True)
class Task:
    """A task represented independently of its document format."""

    id: int
    title: str
    points: int
    due_date: date | None
    status: TaskStatus
    body: str
