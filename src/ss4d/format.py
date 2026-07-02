"""標準出力向けの整形ヘルパー。"""

from datetime import date

import typer

from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


def format_task_lines(tasks: tuple[Task, ...]) -> list[str]:
    """タスク一覧を列揃え済みの表示行へ整形する。"""

    number_width = max(len(format_task_number(task)) for task in tasks)
    point_width = max(len(format_task_point(task)) for task in tasks)
    return [
        format_task_line(
            task,
            number_width=number_width,
            point_width=point_width,
        )
        for task in tasks
    ]


def format_task_line(
    task: Task,
    *,
    number_width: int,
    point_width: int,
) -> str:
    """タスク 1 件を一覧表示用の 1 行テキストへ整形する。"""

    number = format_task_number(task).ljust(number_width)
    point = format_task_point(task).ljust(point_width)
    due_date = format_due_date(task.due_date)
    status = format_status(task.status)
    return f"{number} {point} {task.title} {due_date} {status}"


def format_task_number(task: Task) -> str:
    """一覧表示用のタスク番号テキストを返す。"""

    return f"#{task.id}"


def format_task_point(task: Task) -> str:
    """一覧表示用のタスクポイントテキストを返す。"""

    return f"[{task.points}]"


def format_due_date(due_date: date | None) -> str:
    """一覧表示用の期限日テキストを返す。"""

    if due_date is None:
        return "-"
    return due_date.isoformat()


def format_status(status: TaskStatus) -> str:
    """一覧表示用にステータス名へ Confluence 相当の色を付ける。"""

    status_styles = {
        TaskStatus.TODO: typer.colors.BRIGHT_BLACK,
        TaskStatus.PROGRESS: typer.colors.BLUE,
        TaskStatus.REVIEW: typer.colors.RED,
        TaskStatus.DONE: typer.colors.GREEN,
    }
    return typer.style(status.name, fg=status_styles[status])
