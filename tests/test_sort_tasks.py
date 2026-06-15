from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.process.sort_tasks import sort_tasks


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for sort-task tests."""

        self.should_fail = should_fail
        self.sorted = False

    def append_task(self, number: int, title: str) -> None:
        """Ignore append calls required by the document manager protocol."""

    def sort_tasks(self) -> None:
        """Record the sort request or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.sorted = True


class SortTasksTest(TestCase):
    def test_sort_tasks_updates_document(self) -> None:
        """Sort tasks in the configured document."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            sort_tasks(
                config_path=config_path,
                document_manager=document_manager,
            )

            self.assertTrue(document_manager.sorted)

    def test_failed_document_update_raises_error(self) -> None:
        """Raise the document update error when sorting fails."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager(should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                sort_tasks(
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
