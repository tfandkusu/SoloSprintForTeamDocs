from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.process.create_task import create_task, format_task_heading


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake document manager for create-task tests."""

        self.should_fail = should_fail
        self.heading: str | None = None

    def append_heading(self, heading: str) -> None:
        """Record the heading or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.heading = heading


class CreateTaskTest(TestCase):
    def test_format_task_heading_uses_default_points_without_spaces(self) -> None:
        """Format task headings with default story points and escaped title."""

        self.assertEqual(
            format_task_heading(1, "CI & deploy", due_date=date(2026, 6, 14)),
            '<h1>#1[1]CI &amp; deploy <time datetime="2026-06-14" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
            '<ac:parameter ac:name="title">TODO</ac:parameter>'
            "</ac:structured-macro></h1>",
        )

    def test_create_task_updates_confluence_and_increments_number(self) -> None:
        """Update Confluence and increment the task number after success."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            task_number = create_task(
                "CI setup",
                config_path=config_path,
                document_manager=document_manager,
            )

            self.assertEqual(task_number, 1)
            self.assertEqual(
                document_manager.heading,
                "<h1>#1[1]CI setup "
                f'<time datetime="{date.today().isoformat()}" /> '
                '<ac:structured-macro ac:name="status" ac:schema-version="1">'
                '<ac:parameter ac:name="colour">Grey</ac:parameter>'
                '<ac:parameter ac:name="title">TODO</ac:parameter>'
                "</ac:structured-macro></h1>",
            )
            self.assertIn("number = 2", config_path.read_text(encoding="utf-8"))

    def test_failed_confluence_update_does_not_increment_number(self) -> None:
        """Keep the task number unchanged when the Confluence update fails."""

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
