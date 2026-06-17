from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.process.update_task_due_date import parse_deadline, update_task_due_date


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for update-task-due-date tests."""

        self.should_fail = should_fail
        self.number: int | None = None
        self.due_date: str | None = None

    def append_task(self, number: int, title: str) -> None:
        """Ignore append calls required by the document manager protocol."""

    def sort_tasks(self) -> None:
        """Ignore sort calls required by the document manager protocol."""

    def update_task_status(self, number: int, status: str) -> None:
        """Ignore status calls required by the document manager protocol."""

    def update_task_due_date(self, number: int, due_date: str) -> None:
        """Record the due-date update request or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.number = number
        self.due_date = due_date


class UpdateTaskDueDateTest(TestCase):
    def test_parse_deadline_returns_iso_date(self) -> None:
        """Parse a date expression into an ISO date."""

        self.assertEqual(parse_deadline("2026-06-30"), "2026-06-30")

    def test_unknown_deadline_does_not_update_document(self) -> None:
        """Reject unknown deadlines before updating the document."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            with self.assertRaisesRegex(ValueError, "Could not parse deadline"):
                update_task_due_date(
                    7,
                    "",
                    config_path=config_path,
                    document_manager=document_manager,
                )

            self.assertIsNone(document_manager.number)
            self.assertIsNone(document_manager.due_date)

    def test_update_task_due_date_updates_document(self) -> None:
        """Update a task due date in the configured document."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            due_date = update_task_due_date(
                7,
                "2026-06-30",
                config_path=config_path,
                document_manager=document_manager,
            )

            self.assertEqual(due_date, "2026-06-30")
            self.assertEqual(document_manager.number, 7)
            self.assertEqual(document_manager.due_date, "2026-06-30")

    def test_failed_document_update_raises_error(self) -> None:
        """Raise the document update error when due-date update fails."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager(should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_due_date(
                    7,
                    "2026-06-30",
                    config_path=config_path,
                    document_manager=document_manager,
                )


def _write_config(directory: Path, *, number: int) -> Path:
    """Write a temporary ss4d config file for tests."""

    config_path = directory / ".ss4d.toml"
    config_path.write_text(
        'url = "https://example.atlassian.net/wiki"\n'
        'token = "token"\n'
        'page = "123"\n'
        'email = "user@example.com"\n'
        f"number = {number}\n",
        encoding="utf-8",
    )
    return config_path
