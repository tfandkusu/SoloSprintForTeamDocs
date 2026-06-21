"""Task status domain model."""

from enum import StrEnum


class TaskStatus(StrEnum):
    """Supported workflow statuses for a task."""

    TODO = "todo"
    PROGRESS = "progress"
    REVIEW = "review"
    DONE = "done"


def normalize_task_status(status: str) -> str:
    """Return a supported uppercase task status name."""

    status_name = status.upper()
    if status_name not in TaskStatus.__members__:
        allowed_statuses = ", ".join(TaskStatus.__members__)
        raise ValueError(f"Status must be one of: {allowed_statuses}.")
    return status_name
