"""スプリントのポイント計算処理。"""

from collections.abc import Iterable

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


def calculate_done_point(tasks: Iterable[Task]) -> int:
    """完了済みタスクの合計ポイントを計算する。"""

    return sum(task.points for task in tasks if task.status == TaskStatus.DONE)


def calculate_all_point(tasks: Iterable[Task]) -> int:
    """すべてのタスクの合計ポイントを計算する。"""

    return sum(task.points for task in tasks)


def calculate_remaining_point(tasks: Iterable[Task]) -> int:
    """未完了タスクの合計ポイントを計算する。"""

    return sum(task.points for task in tasks if task.status != TaskStatus.DONE)


def with_calculated_points(sprint: Sprint) -> Sprint:
    """タスク一覧からポイントを再計算したスプリントを返す。"""

    return Sprint(
        start_day=sprint.start_day,
        done_point=calculate_done_point(sprint.tasks),
        remaining_point=calculate_remaining_point(sprint.tasks),
        all_point=calculate_all_point(sprint.tasks),
        tasks=sprint.tasks,
    )
