from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.update_task_due_date import parse_deadline, update_task_due_date


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for update-task-due-date tests."""

        self.should_fail = should_fail
        self.tasks = [_task(7), _task(8, due_date=date(2026, 7, 1))]
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


class UpdateTaskDueDateTest(TestCase):
    def test_parse_deadline_returns_iso_date(self) -> None:
        """Parse a date expression into an ISO date."""

        self.assertEqual(parse_deadline("2026-06-30"), "2026-06-30")

    def test_update_task_due_date_replaces_only_matching_domain_model(self) -> None:
        """Update the matching due date while preserving every other field."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            original_tasks = manager.tasks.copy()
            due_date = update_task_due_date(
                7,
                "2026-06-30",
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual(due_date, "2026-06-30")
        self.assertEqual(manager.tasks[0].due_date, date(2026, 6, 30))
        self.assertEqual(
            manager.tasks[0],
            replace(original_tasks[0], due_date=date(2026, 6, 30)),
        )
        self.assertEqual(manager.tasks[1], original_tasks[1])
        self.assertEqual(manager.write_count, 1)

    def test_unknown_deadline_does_not_update_document(self) -> None:
        """Reject unknown deadlines before reading or writing the document."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(ValueError, "Could not parse deadline"):
                update_task_due_date(
                    7,
                    "",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_missing_task_does_not_update_document(self) -> None:
        """Reject a missing task number without writing the document."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(RuntimeError, "Task #9 was not found"):
                update_task_due_date(
                    9,
                    "2026-06-30",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_failed_document_update_raises_error(self) -> None:
        """Raise the document update error when writing updated tasks fails."""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(should_fail=True)
            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_due_date(
                    7,
                    "2026-06-30",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(number: int, *, due_date: date | None = None) -> Task:
    """Create a task fixture with fields that updates must preserve."""

    return Task(
        id=number,
        title=f"Task {number}",
        points=3,
        due_date=due_date,
        status=TaskStatus.REVIEW,
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
