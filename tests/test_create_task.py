from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.process.create_task import create_task


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for create-task tests."""

        self.should_fail = should_fail
        self.number: int | None = None
        self.title: str | None = None

    def append_task(self, number: int, title: str) -> None:
        """Record the task or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.number = number
        self.title = title

    def sort_tasks(self) -> None:
        """Ignore sort calls required by the document manager protocol."""

    def update_task_status(self, number: int, status: str) -> None:
        """Ignore status calls required by the document manager protocol."""


class CreateTaskTest(TestCase):
    def test_create_task_updates_document_and_increments_number(self) -> None:
        """Update the document and increment the task number after success."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            task_number = create_task(
                "CI setup",
                config_path=config_path,
                document_manager=document_manager,
            )

            self.assertEqual(task_number, 1)
            self.assertEqual(document_manager.number, 1)
            self.assertEqual(document_manager.title, "CI setup")
            self.assertIn("number = 2", config_path.read_text(encoding="utf-8"))

    def test_failed_document_update_does_not_increment_number(self) -> None:
        """Keep the task number unchanged when the document update fails."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager(should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                create_task(
                    "CI setup",
                    config_path=config_path,
                    document_manager=document_manager,
                )

            self.assertIn("number = 1", config_path.read_text(encoding="utf-8"))


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
