"""タスクのドメインモデル。"""

from dataclasses import dataclass
from datetime import date

from ss4d.model.task_status import TaskStatus


@dataclass(frozen=True)
class Task:
    """ドキュメント形式から独立して表現されたタスク。"""

    id: int
    title: str
    points: int
    due_date: date | None
    status: TaskStatus
    body: str
