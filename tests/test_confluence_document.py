from typing import Any
from unittest import TestCase

from ss4d.document.confluence import ConfluenceDocumentManager


class FakeConfluenceClient:
    def __init__(self) -> None:
        """Create a fake Confluence client for document manager tests."""

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
        """Record the update request."""

        self.page_id = page_id
        self.updated_title = title
        self.updated_body = body
        self.representation = representation
        self.minor_edit = minor_edit
        return object()


class ConfluenceDocumentManagerTest(TestCase):
    def test_append_heading_updates_configured_page_storage_body(self) -> None:
        """Append a heading to the configured Confluence page."""

        client = FakeConfluenceClient()
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.append_heading("<h1>Task</h1>")

        self.assertEqual(client.page_id, "123")
        self.assertEqual(client.expand, "body.storage,version")
        self.assertEqual(client.updated_title, "Sprint page")
        self.assertEqual(client.updated_body, "<p>Existing</p><h1>Task</h1>")
        self.assertEqual(client.representation, "storage")
        self.assertFalse(client.minor_edit)
