from datetime import date
from typing import Any
from unittest import TestCase

from ss4d.document.confluence import ConfluenceDocumentManager, format_task_heading


class FakeConfluenceClient:
    def __init__(self, *, page: dict[str, Any] | None = None) -> None:
        """Create a fake Confluence client for document manager tests."""

        self.page = page or {
            "title": "Sprint page",
            "body": {"storage": {"value": "<p>Existing</p>"}},
        }
        self.page_id: str | None = None
        self.expand: str | None = None
        self.updated_title: str | None = None
        self.updated_body: str | None = None
        self.representation: str | None = None
        self.minor_edit: bool | None = None

    def get_page_by_id(self, page_id: str, expand: str) -> dict[str, Any]:
        """Record the fetch request and return a stored page response."""

        self.page_id = page_id
        self.expand = expand
        return self.page

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        *,
        representation: str,
        minor_edit: bool,
    ) -> object:
        """Record the update request."""

        self.page_id = page_id
        self.updated_title = title
        self.updated_body = body
        self.representation = representation
        self.minor_edit = minor_edit
        return object()


class ConfluenceDocumentManagerTest(TestCase):
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

    def test_append_task_updates_configured_page_storage_body(self) -> None:
        """Append a task heading to the configured Confluence page."""

        client = FakeConfluenceClient()
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.append_task(1, "CI setup")

        self.assertEqual(client.page_id, "123")
        self.assertEqual(client.expand, "body.storage,version")
        self.assertEqual(client.updated_title, "Sprint page")
        self.assertEqual(
            client.updated_body,
            "<p>Existing</p><h1>#1[1]CI setup "
            f'<time datetime="{date.today().isoformat()}" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
            '<ac:parameter ac:name="title">TODO</ac:parameter>'
            "</ac:structured-macro></h1>",
        )
        self.assertEqual(client.representation, "storage")
        self.assertFalse(client.minor_edit)

    def test_append_task_uses_empty_body_when_storage_body_is_missing(self) -> None:
        """Append a task heading when the Confluence storage body is missing."""

        client = FakeConfluenceClient(page={"title": "Sprint page", "body": {}})
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.append_task(1, "CI setup")

        self.assertEqual(
            client.updated_body,
            "<h1>#1[1]CI setup "
            f'<time datetime="{date.today().isoformat()}" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
            '<ac:parameter ac:name="title">TODO</ac:parameter>'
            "</ac:structured-macro></h1>",
        )
