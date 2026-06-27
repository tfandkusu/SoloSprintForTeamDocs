"""タスクステータスのドメインモデル。"""

from enum import StrEnum


class TaskStatus(StrEnum):
    """タスクでサポートするワークフローステータス。"""

    TODO = "todo"
    PROGRESS = "progress"
    REVIEW = "review"
    DONE = "done"


def normalize_task_status(status: str) -> str:
    """サポートされる大文字のタスクステータス名を返す。"""

    status_name = status.upper()
    if status_name not in TaskStatus.__members__:
        allowed_statuses = ", ".join(TaskStatus.__members__)
        raise ValueError(f"Status must be one of: {allowed_statuses}.")
    return status_name
