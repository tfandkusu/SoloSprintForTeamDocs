from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.update_task_status import update_task_status


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for update-task-status tests."""

        self.should_fail = should_fail
        self.tasks = [_task(7), _task(8, status=TaskStatus.PROGRESS)]
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


class UpdateTaskStatusTest(TestCase):
    def test_update_task_status_replaces_only_matching_domain_model(self) -> None:
        """Update the matching status while preserving every other task field."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            original_tasks = manager.tasks.copy()
            updated_status = update_task_status(
                7,
                "done",
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual(updated_status, "DONE")
        self.assertEqual(manager.tasks[0].status, TaskStatus.DONE)
        self.assertEqual(
            manager.tasks[0],
            replace(original_tasks[0], status=TaskStatus.DONE),
        )
        self.assertEqual(manager.tasks[1], original_tasks[1])
        self.assertEqual(manager.write_count, 1)

    def test_unknown_status_does_not_update_document(self) -> None:
        """Reject unknown statuses before reading or writing the document."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(ValueError, "Status must be one of"):
                update_task_status(
                    7,
                    "blocked",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_missing_task_does_not_update_document(self) -> None:
        """Reject a missing task number without writing the document."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(RuntimeError, "Task #9 was not found"):
                update_task_status(
                    9,
                    "DONE",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_failed_document_update_raises_error(self) -> None:
        """Raise the document update error when writing updated tasks fails."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(should_fail=True)
            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_status(
                    7,
                    "DONE",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(number: int, *, status: TaskStatus = TaskStatus.TODO) -> Task:
    """Create a task fixture with fields that updates must preserve."""

    return Task(
        id=number,
        title=f"Task {number}",
        points=3,
        due_date=date(2026, 6, 30),
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
