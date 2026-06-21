"""Task domain model."""

from dataclasses import dataclass
from datetime import date

from ss4d.model.task_status import TaskStatus


@dataclass(frozen=True)
class Task:
    """A task represented independently of its document format."""

    id: int
    title: str
    points: int
    due_date: date | None
    status: TaskStatus
    body: str
