from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import TestCase

from ss4d.config import Config
from ss4d.process.add_task import create_task, format_task_heading


class FakeConfluenceClient:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.page_id: str | None = None
        self.updated_title: str | None = None
        self.updated_body: str | None = None
        self.representation: str | None = None
        self.minor_edit: bool | None = None

    def get_page_by_id(self, page_id: str, expand: str) -> dict[str, Any]:
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
        if self.should_fail:
            raise RuntimeError("Confluence update failed")

        self.page_id = page_id
        self.updated_title = title
        self.updated_body = body
        self.representation = representation
        self.minor_edit = minor_edit
        return object()


class AddTaskTest(TestCase):
    def test_format_task_heading_uses_default_points_without_spaces(self) -> None:
        self.assertEqual(
            format_task_heading(1, "CI & deploy"),
            "<h1>#1[1]CI &amp; deploy</h1>",
        )

    def test_create_task_updates_confluence_and_increments_number(self) -> None:
        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            client = FakeConfluenceClient()
            seen_config: Config | None = None

            def client_factory(config: Config) -> FakeConfluenceClient:
                nonlocal seen_config
                seen_config = config
                return client

            heading = create_task(
                "CI setup",
                config_path=config_path,
                client_factory=client_factory,
            )

            self.assertEqual(heading, "<h1>#1[1]CI setup</h1>")
            self.assertEqual(
                seen_config,
                Config(
                    url="https://example.atlassian.net/wiki",
                    token="token",
                    page="123",
                    number=1,
                ),
            )
            self.assertEqual(client.page_id, "123")
            self.assertEqual(client.updated_title, "Sprint page")
            self.assertEqual(
                client.updated_body,
                "<p>Existing</p><h1>#1[1]CI setup</h1>",
            )
            self.assertEqual(client.representation, "storage")
            self.assertFalse(client.minor_edit)
            self.assertIn("number = 2", config_path.read_text(encoding="utf-8"))

    def test_failed_confluence_update_does_not_increment_number(self) -> None:
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
    config_path = directory / ".ss4d.toml"
    config_path.write_text(
        'url = "https://example.atlassian.net/wiki"\n'
        'token = "token"\n'
        'page = "123"\n'
        f"number = {number}\n",
        encoding="utf-8",
    )
    return config_path
