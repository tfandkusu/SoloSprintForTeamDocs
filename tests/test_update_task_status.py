from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.process.update_task_status import update_task_status


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for update-task-status tests."""

        self.should_fail = should_fail
        self.number: int | None = None
        self.status: str | None = None

    def append_task(self, number: int, title: str) -> None:
        """Ignore append calls required by the document manager protocol."""

    def sort_tasks(self) -> None:
        """Ignore sort calls required by the document manager protocol."""

    def update_task_status(self, number: int, status: str) -> None:
        """Record the status update request or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.number = number
        self.status = status


class UpdateTaskStatusTest(TestCase):
    def test_update_task_status_updates_document(self) -> None:
        """Update a task status in the configured document."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            updated_status = update_task_status(
                7,
                "done",
                config_path=config_path,
                document_manager=document_manager,
            )

            self.assertEqual(updated_status, "DONE")
            self.assertEqual(document_manager.number, 7)
            self.assertEqual(document_manager.status, "DONE")

    def test_unknown_status_does_not_update_document(self) -> None:
        """Reject unknown statuses before updating the document."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            with self.assertRaisesRegex(ValueError, "Status must be one of"):
                update_task_status(
                    7,
                    "blocked",
                    config_path=config_path,
                    document_manager=document_manager,
                )

            self.assertIsNone(document_manager.number)
            self.assertIsNone(document_manager.status)

    def test_failed_document_update_raises_error(self) -> None:
        """Raise the document update error when status update fails."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager(should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_status(
                    7,
                    "DONE",
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
