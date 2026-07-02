from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.list_tasks import list_tasks


class FakeDocumentManager:
    def __init__(self, tasks: tuple[Task, ...]) -> None:
        """list テスト用の偽ドキュメントマネージャーを作成する。"""

        self.sprint = Sprint(
            start_day=date(2026, 7, 1),
            done_point=0,
            remaining_point=99,
            all_point=99,
            tasks=tasks,
        )

    def read_sprint(self) -> Sprint:
        """設定済みのスプリントを返す。"""

        return self.sprint

    def write_sprint(self, sprint: Sprint) -> None:
        """書き込み API を満たすが、このテストでは呼ばれない。"""

        msg = "write_sprint should not be called by list_tasks"
        raise AssertionError(msg)


class ListTasksTest(TestCase):
    def test_list_tasks_returns_remaining_tasks_by_default(self) -> None:
        """未完了タスクだけを返す。"""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory))
            tasks = (
                _task(1, "Backlog", status=TaskStatus.TODO),
                _task(2, "Fix bug", status=TaskStatus.PROGRESS),
                _task(3, "Release", status=TaskStatus.DONE),
            )

            listed_tasks = list_tasks(
                config_path=config_path,
                document_manager=FakeDocumentManager(tasks),
            )

        self.assertEqual(tuple(task.id for task in listed_tasks), (1, 2))

    def test_list_tasks_returns_all_tasks_when_requested(self) -> None:
        """all 指定時は完了済みを含むすべてのタスクを返す。"""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory))
            tasks = (
                _task(1, "Backlog", status=TaskStatus.TODO),
                _task(2, "Release", status=TaskStatus.DONE),
            )

            listed_tasks = list_tasks(
                show_all=True,
                config_path=config_path,
                document_manager=FakeDocumentManager(tasks),
            )

        self.assertEqual(tuple(task.id for task in listed_tasks), (1, 2))


def _task(
    number: int,
    title: str,
    *,
    status: TaskStatus,
    due_date: date | None = date(2026, 7, 3),
) -> Task:
    """テスト用タスクを作成する。"""

    return Task(
        id=number,
        title=title,
        points=1,
        due_date=due_date,
        status=status,
        body="",
    )


def _write_config(directory: Path) -> Path:
    """テスト用の一時 ss4d 設定ファイルを書き込む。"""

    config_path = directory / ".ss4d.toml"
    config_path.write_text(
        "\n".join(
            [
                'url = "https://example.atlassian.net"',
                'token = "token"',
                'page = "123"',
                "number = 7",
                'email = "user@example.com"',
            ]
        ),
        encoding="utf-8",
    )
    return config_path
