from datetime import date
from typing import Any
from unittest import TestCase

from ss4d.document.confluence import ConfluenceDocumentManager
from ss4d.document.confluence_html_builder import format_storage_tasks
from ss4d.document.confluence_html_parser import parse_storage_tasks
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


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
    def test_read_tasks_converts_document_to_domain_models(self) -> None:
        """Read every document task including its free-form HTML body."""

        client = FakeConfluenceClient(
            page={
                "title": "Sprint page",
                "body": {
                    "storage": {
                        "value": (
                            "<p>Intro is not a task</p>"
                            "<h1>#2[3]Deploy &amp; verify "
                            '<time datetime="2026-06-30" /> '
                            f"{_status_macro('PROGRESS')}</h1>"
                            "<p>Keep this body</p>"
                        )
                    }
                },
            }
        )
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        self.assertEqual(
            manager.read_tasks(),
            [
                Task(
                    id=2,
                    title="Deploy & verify",
                    points=3,
                    due_date=date(2026, 6, 30),
                    status=TaskStatus.PROGRESS,
                    body="<p>Keep this body</p>",
                )
            ],
        )
        self.assertEqual(client.page_id, "123")
        self.assertEqual(client.expand, "body.storage,version")

    def test_write_tasks_replaces_document_from_domain_models(self) -> None:
        """Replace the complete document using supplied task models."""

        client = FakeConfluenceClient()
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.write_tasks(
            [
                Task(
                    id=1,
                    title="CI & deploy",
                    points=2,
                    due_date=None,
                    status=TaskStatus.REVIEW,
                    body="<p>Task body</p>",
                )
            ]
        )

        self.assertEqual(client.updated_title, "Sprint page")
        self.assertEqual(
            client.updated_body,
            "<h1>#1[2]CI &amp; deploy "
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Red</ac:parameter>'
            '<ac:parameter ac:name="title">REVIEW</ac:parameter>'
            "</ac:structured-macro></h1><p>Task body</p>",
        )
        self.assertEqual(client.representation, "storage")
        self.assertFalse(client.minor_edit)

    def test_storage_tasks_round_trip_all_domain_fields(self) -> None:
        """Round-trip supported task fields through Confluence storage HTML."""

        tasks = [
            Task(
                id=7,
                title="Escaped <title>",
                points=5,
                due_date=date(2026, 7, 1),
                status=TaskStatus.DONE,
                body="<p><strong>Finished</strong></p>",
            )
        ]

        self.assertEqual(parse_storage_tasks(format_storage_tasks(tasks)), tasks)


def _status_macro(status: str) -> str:
    """Format a status macro fixture."""

    return (
        '<ac:structured-macro ac:name="status" ac:schema-version="1">'
        f'<ac:parameter ac:name="title">{status}</ac:parameter>'
        "</ac:structured-macro>"
    )
