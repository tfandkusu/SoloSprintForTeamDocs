"""Confluence document manager."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from html import escape
from importlib import import_module
from typing import Protocol, cast

from ss4d.config import Config

STORY_POINTS = 1


class ConfluenceClient(Protocol):
    """Small subset of ConfluenceCloud used by the document manager."""

    def get_page_by_id(self, page_id: str, expand: str) -> Mapping[str, object]:
        """Fetch a Confluence page."""
        ...

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        *,
        representation: str,
        minor_edit: bool,
    ) -> object:
        """Update a Confluence page."""
        ...


@dataclass(frozen=True)
class ConfluenceDocumentManager:
    """Document manager implementation backed by Confluence."""

    client: ConfluenceClient
    page_id: str

    def append_task(self, number: int, title: str) -> None:
        """Append a task heading to the configured Confluence page."""

        heading = format_task_heading(number, title)
        page = self.client.get_page_by_id(
            self.page_id,
            expand="body.storage,version",
        )
        self.client.update_page(
            self.page_id,
            _extract_page_title(page),
            _append_storage_body(page, heading),
            representation="storage",
            minor_edit=False,
        )


def create_confluence_document_manager(config: Config) -> ConfluenceDocumentManager:
    """Create a Confluence document manager from configuration."""

    return ConfluenceDocumentManager(
        client=create_confluence_client(config),
        page_id=config.page,
    )


def create_confluence_client(config: Config) -> ConfluenceClient:
    """Create an authenticated Confluence client from configuration."""

    confluence_module = import_module("atlassian")
    confluence = getattr(confluence_module, "Confluence")
    return cast(
        ConfluenceClient,
        confluence(
            url=config.url,
            username=config.email,
            password=config.token,
            cloud=True,
        ),
    )


def format_task_heading(
    number: int, title: str, *, due_date: date | None = None
) -> str:
    """Format the Confluence storage h1 for a task."""

    task_due_date = due_date or date.today()
    return (
        f"<h1>#{number}[{STORY_POINTS}]{escape(title)} "
        f'<time datetime="{task_due_date.isoformat()}" /> '
        '<ac:structured-macro ac:name="status" ac:schema-version="1">'
        '<ac:parameter ac:name="colour">Grey</ac:parameter>'
        '<ac:parameter ac:name="title">TODO</ac:parameter>'
        "</ac:structured-macro>"
        "</h1>"
    )


def _append_storage_body(page: Mapping[str, object], heading: str) -> str:
    """Append a heading to the page storage body."""

    current_body = _extract_storage_body(page)
    return f"{current_body}{heading}"


def _extract_page_title(page: Mapping[str, object]) -> str:
    """Extract the Confluence page title from an API response."""

    title = page.get("title")
    if not isinstance(title, str) or title == "":
        raise RuntimeError("Confluence page response did not include a title.")
    return title


def _extract_storage_body(page: Mapping[str, object]) -> str:
    """Extract the storage-format body from an API response."""

    body = page.get("body")
    if not isinstance(body, Mapping):
        return ""

    typed_body = cast(Mapping[str, object], body)
    storage = typed_body.get("storage")
    if not isinstance(storage, Mapping):
        return ""

    typed_storage = cast(Mapping[str, object], storage)
    value = typed_storage.get("value")
    if not isinstance(value, str):
        return ""

    return value
