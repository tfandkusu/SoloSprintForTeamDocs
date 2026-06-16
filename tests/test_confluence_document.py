from datetime import date
from typing import Any
from unittest import TestCase

from ss4d.document.confluence import (
    ConfluenceDocumentManager,
    format_task_heading,
    sort_storage_body,
    update_storage_task_status,
)


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

    def test_sort_tasks_updates_configured_page_storage_body(self) -> None:
        """Sort task sections in the configured Confluence page."""

        client = FakeConfluenceClient(
            page={
                "title": "Sprint page",
                "body": {
                    "storage": {
                        "value": (
                            "<p>Intro</p>"
                            '<h1>#2 Later <time datetime="2026-06-20" /></h1>'
                            "<p>Later body</p>"
                            '<h1>#1 Earlier <time datetime="2026-06-18" /></h1>'
                            "<p>Earlier body</p>"
                        )
                    }
                },
            }
        )
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.sort_tasks()

        self.assertEqual(client.page_id, "123")
        self.assertEqual(client.expand, "body.storage,version")
        self.assertEqual(client.updated_title, "Sprint page")
        self.assertEqual(
            client.updated_body,
            "<p>Intro</p>"
            '<h1>#1 Earlier <time datetime="2026-06-18" /></h1>'
            "<p>Earlier body</p>"
            '<h1>#2 Later <time datetime="2026-06-20" /></h1>'
            "<p>Later body</p>",
        )
        self.assertEqual(client.representation, "storage")
        self.assertFalse(client.minor_edit)

    def test_update_task_status_updates_configured_page_storage_body(self) -> None:
        """Update a task status in the configured Confluence page."""

        client = FakeConfluenceClient(
            page={
                "title": "Sprint page",
                "body": {
                    "storage": {
                        "value": (
                            "<p>Intro</p>"
                            '<h1>#1[1]First <time datetime="2026-06-18" /> '
                            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
                            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
                            '<ac:parameter ac:name="title">TODO</ac:parameter>'
                            "</ac:structured-macro></h1>"
                            "<p>First body</p>"
                            '<h1>#2[1]Second <time datetime="2026-06-19" /> '
                            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
                            '<ac:parameter ac:name="colour">Blue</ac:parameter>'
                            '<ac:parameter ac:name="title">PROGRESS</ac:parameter>'
                            "</ac:structured-macro></h1>"
                        )
                    }
                },
            }
        )
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.update_task_status(1, "review")

        self.assertEqual(client.page_id, "123")
        self.assertEqual(client.expand, "body.storage,version")
        self.assertEqual(client.updated_title, "Sprint page")
        self.assertEqual(
            client.updated_body,
            "<p>Intro</p>"
            '<h1>#1[1]First <time datetime="2026-06-18"></time> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Red</ac:parameter>'
            '<ac:parameter ac:name="title">REVIEW</ac:parameter>'
            "</ac:structured-macro></h1>"
            "<p>First body</p>"
            '<h1>#2[1]Second <time datetime="2026-06-19" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Blue</ac:parameter>'
            '<ac:parameter ac:name="title">PROGRESS</ac:parameter>'
            "</ac:structured-macro></h1>",
        )
        self.assertEqual(client.representation, "storage")
        self.assertFalse(client.minor_edit)

    def test_sort_storage_body_sorts_h1_sections_by_due_date(self) -> None:
        """Sort each h1-led section by nearest due date."""

        body = (
            "<p>Intro</p>\n"
            '<h1>#2 Later <time datetime="2026-06-20" /></h1>\n'
            "<p>Later body</p>\n"
            '<h1>#1 Earlier <time datetime="2026-06-18" /></h1>\n'
            "<p>Earlier body</p>\n"
            "<h1>#3 Missing date</h1>\n"
            "<p>Missing body</p>\n"
        )

        self.assertEqual(
            sort_storage_body(body),
            "<p>Intro</p>\n"
            '<h1>#1 Earlier <time datetime="2026-06-18" /></h1>\n'
            "<p>Earlier body</p>\n"
            '<h1>#2 Later <time datetime="2026-06-20" /></h1>\n'
            "<p>Later body</p>\n"
            "<h1>#3 Missing date</h1>\n"
            "<p>Missing body</p>\n",
        )

    def test_sort_storage_body_sorts_done_tasks_after_other_statuses(self) -> None:
        """Sort done sections after non-done sections, then by nearest due date."""

        body = (
            "<p>Intro</p>\n"
            '<h1>#4 Done later <time datetime="2026-06-22" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Green</ac:parameter>'
            '<ac:parameter ac:name="title">DONE</ac:parameter>'
            "</ac:structured-macro></h1>\n"
            "<p>Done later body</p>\n"
            '<h1>#1 Review soon <time datetime="2026-06-18" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Red</ac:parameter>'
            '<ac:parameter ac:name="title">REVIEW</ac:parameter>'
            "</ac:structured-macro></h1>\n"
            "<p>Review soon body</p>\n"
            '<h1>#2 Done earlier <time datetime="2026-06-10" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Green</ac:parameter>'
            '<ac:parameter ac:name="title">DONE</ac:parameter>'
            "</ac:structured-macro></h1>\n"
            "<p>Done earlier body</p>\n"
        )

        self.assertEqual(
            sort_storage_body(body),
            "<p>Intro</p>\n"
            '<h1>#1 Review soon <time datetime="2026-06-18" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Red</ac:parameter>'
            '<ac:parameter ac:name="title">REVIEW</ac:parameter>'
            "</ac:structured-macro></h1>\n"
            "<p>Review soon body</p>\n"
            '<h1>#2 Done earlier <time datetime="2026-06-10" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Green</ac:parameter>'
            '<ac:parameter ac:name="title">DONE</ac:parameter>'
            "</ac:structured-macro></h1>\n"
            "<p>Done earlier body</p>\n"
            '<h1>#4 Done later <time datetime="2026-06-22" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Green</ac:parameter>'
            '<ac:parameter ac:name="title">DONE</ac:parameter>'
            "</ac:structured-macro></h1>\n"
            "<p>Done later body</p>\n",
        )

    def test_update_storage_task_status_replaces_matching_task_status(self) -> None:
        """Replace only the matching task section status macro."""

        body = (
            "<p>Intro</p>"
            '<h1>#1[1]First <time datetime="2026-06-18" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
            '<ac:parameter ac:name="title">TODO</ac:parameter>'
            "</ac:structured-macro></h1>"
            '<h1>#10[1]Tenth <time datetime="2026-06-19" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
            '<ac:parameter ac:name="title">TODO</ac:parameter>'
            "</ac:structured-macro></h1>"
        )

        self.assertEqual(
            update_storage_task_status(body, 1, "DONE"),
            "<p>Intro</p>"
            '<h1>#1[1]First <time datetime="2026-06-18"></time> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Green</ac:parameter>'
            '<ac:parameter ac:name="title">DONE</ac:parameter>'
            "</ac:structured-macro></h1>"
            '<h1>#10[1]Tenth <time datetime="2026-06-19" /> '
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Grey</ac:parameter>'
            '<ac:parameter ac:name="title">TODO</ac:parameter>'
            "</ac:structured-macro></h1>",
        )

    def test_update_storage_task_status_inserts_missing_status_macro(self) -> None:
        """Insert a status macro when the matching h1 has none."""

        self.assertEqual(
            update_storage_task_status("<h1>#1[1]First</h1><p>Body</p>", 1, "DONE"),
            '<h1>#1[1]First <ac:structured-macro ac:name="status" '
            'ac:schema-version="1"><ac:parameter ac:name="colour">Green'
            '</ac:parameter><ac:parameter ac:name="title">DONE</ac:parameter>'
            "</ac:structured-macro></h1><p>Body</p>",
        )

    def test_update_storage_task_status_rejects_unknown_status(self) -> None:
        """Reject status names that are not supported."""

        with self.assertRaisesRegex(ValueError, "Status must be one of"):
            update_storage_task_status("<h1>#1[1]First</h1>", 1, "BLOCKED")

    def test_update_storage_task_status_rejects_missing_task(self) -> None:
        """Reject updates for a task number that is not in the body."""

        with self.assertRaisesRegex(RuntimeError, "Task #2 was not found."):
            update_storage_task_status("<h1>#1[1]First</h1>", 2, "DONE")
