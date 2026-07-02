from datetime import date
from unittest import TestCase

import typer

from ss4d.format import format_due_date, format_task_lines
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


class FormatTest(TestCase):
    def test_format_task_lines_aligns_number_and_point_only(self) -> None:
        """番号とポイントを揃えつつ締め切り日は固定幅にしない。"""

        tasks = (
            _task(7, "CI setup", points=3, status=TaskStatus.PROGRESS),
            _task(12, "Release prep", points=10, status=TaskStatus.REVIEW),
        )

        lines = format_task_lines(tasks)

        self.assertEqual(
            lines,
            [
                f"#7  [3]  CI setup - {typer.style('PROGRESS', fg=typer.colors.BLUE)}",
                f"#12 [10] Release prep - {typer.style('REVIEW', fg=typer.colors.RED)}",
            ],
        )

    def test_format_due_date_outputs_dash_for_missing_date(self) -> None:
        """期限日がない場合はダッシュを返す。"""

        self.assertEqual(format_due_date(None), "-")


def _task(
    number: int,
    title: str,
    *,
    points: int,
    status: TaskStatus,
    due_date: date | None = None,
) -> Task:
    """整形テスト用のタスクを作成する。"""

    return Task(
        id=number,
        title=title,
        points=points,
        due_date=due_date,
        status=status,
        body="",
    )
