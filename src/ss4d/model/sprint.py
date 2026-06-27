"""スプリントのドメインモデル。"""

from dataclasses import dataclass
from datetime import date

from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


@dataclass(frozen=True)
class Sprint:
    """ドキュメント形式から独立して表現されたスプリント。"""

    start_day: date
    done_point: int
    all_point: int
    tasks: list[Task]


def calculate_done_point(tasks: list[Task]) -> int:
    """完了済みタスクの合計ポイントを計算する。"""

    return sum(task.points for task in tasks if task.status == TaskStatus.DONE)


def calculate_all_point(tasks: list[Task]) -> int:
    """すべてのタスクの合計ポイントを計算する。"""

    return sum(task.points for task in tasks)


def with_calculated_points(sprint: Sprint) -> Sprint:
    """タスク一覧からポイントを再計算したスプリントを返す。"""

    return Sprint(
        start_day=sprint.start_day,
        done_point=calculate_done_point(sprint.tasks),
        all_point=calculate_all_point(sprint.tasks),
        tasks=sprint.tasks,
    )
