from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.sort_tasks import sort_tasks


class FakeDocumentManager:
    def __init__(self, tasks: list[Task], *, should_fail: bool = False) -> None:
        """Create a fake document manager for sort-task tests."""

        self.tasks = tasks
        self.should_fail = should_fail
        self.write_count = 0

    def read_tasks(self) -> list[Task]:
        """Return a copy of the configured tasks."""

        return self.tasks.copy()

    def write_tasks(self, tasks: list[Task]) -> None:
        """Record replacement tasks or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.tasks = tasks
        self.write_count += 1


class SortTasksTest(TestCase):
    def test_sort_tasks_updates_domain_models_by_status_and_due_date(self) -> None:
        """Sort non-done tasks before done tasks and missing due dates last."""

        tasks = [
            _task(1, due_date=date(2026, 6, 20)),
            _task(2, due_date=None),
            _task(3, due_date=date(2026, 6, 18)),
            _task(4, due_date=date(2026, 6, 18)),
            _task(5, due_date=date(2026, 6, 10), status=TaskStatus.DONE),
        ]

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(tasks)
            sort_tasks(
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual([task.id for task in manager.tasks], [3, 4, 1, 2, 5])
        self.assertEqual(manager.write_count, 1)

    def test_failed_document_update_raises_error(self) -> None:
        """Raise the document update error when writing sorted tasks fails."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager([_task(1)], should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                sort_tasks(
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(
    number: int,
    *,
    due_date: date | None = None,
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    """Create a task fixture with sortable fields."""

    return Task(
        id=number,
        title=f"Task {number}",
        points=number,
        due_date=due_date,
        status=status,
        body=f"<p>Body {number}</p>",
    )


def _write_config(directory: Path) -> Path:
    """Write a temporary ss4d config file for tests."""

    config_path = directory / ".ss4d.toml"
    config_path.write_text(
        'url = "https://example.atlassian.net/wiki"\n'
        'token = "token"\n'
        'page = "123"\n'
        'email = "user@example.com"\n'
        "number = 1\n",
        encoding="utf-8",
    )
    return config_path
