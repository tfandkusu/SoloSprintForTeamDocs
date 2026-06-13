from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import TestCase

from ss4d.config import Config
from ss4d.process.create_task import create_task, format_task_heading


class FakeConfluenceClient:
    def __init__(self, *, should_fail: bool = False) -> None:
        """Create a fake Confluence client for create-task tests."""

        self.should_fail = should_fail
        self.page_id: str | None = None
        self.updated_title: str | None = None
        self.updated_body: str | None = None
        self.representation: str | None = None
        self.minor_edit: bool | None = None

    def get_page_by_id(self, page_id: str, expand: str) -> dict[str, Any]:
        """Record the fetch request and return a stored page response."""

        self.page_id = page_id
        self.expand = expand
        return {
            "title": "Sprint page",
            "body": {"storage": {"value": "<p>Existing</p>"}},
        }

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        *,
        representation: str,
        minor_edit: bool,
    ) -> object:
        """Record the update request or raise the configured failure."""

        if self.should_fail:
            raise RuntimeError("Confluence update failed")

        self.page_id = page_id
        self.updated_title = title
        self.updated_body = body
        self.representation = representation
        self.minor_edit = minor_edit
        return object()


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
            client = FakeConfluenceClient()
            seen_config: Config | None = None

            def client_factory(config: Config) -> FakeConfluenceClient:
                """Capture the config and return the fake client."""

                nonlocal seen_config
                seen_config = config
                return client

            heading = create_task(
                "CI setup",
                config_path=config_path,
                client_factory=client_factory,
            )

            self.assertIn("#1[1]CI setup", heading)
            self.assertIn("<time datetime=", heading)
            self.assertIn('<ac:parameter ac:name="colour">Grey</ac:parameter>', heading)
            self.assertIn('<ac:parameter ac:name="title">TODO</ac:parameter>', heading)
            self.assertEqual(
                seen_config,
                Config(
                    url="https://example.atlassian.net/wiki",
                    token="token",
                    page="123",
                    number=1,
                    email="user@example.com",
                ),
            )
            self.assertEqual(client.page_id, "123")
            self.assertEqual(client.updated_title, "Sprint page")
            self.assertEqual(
                client.updated_body,
                f"<p>Existing</p>{heading}",
            )
            self.assertEqual(client.representation, "storage")
            self.assertFalse(client.minor_edit)
            self.assertIn("number = 2", config_path.read_text(encoding="utf-8"))

    def test_failed_confluence_update_does_not_increment_number(self) -> None:
        """Keep the task number unchanged when the Confluence update fails."""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            client = FakeConfluenceClient(should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Confluence update failed"):
                create_task(
                    "CI setup",
                    config_path=config_path,
                    client_factory=lambda _config: client,
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
