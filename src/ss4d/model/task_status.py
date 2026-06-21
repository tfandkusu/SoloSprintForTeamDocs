"""Task status domain model."""

from enum import StrEnum


class TaskStatus(StrEnum):
    """Supported workflow statuses for a task."""

    TODO = "todo"
    PROGRESS = "progress"
    REVIEW = "review"
    DONE = "done"
