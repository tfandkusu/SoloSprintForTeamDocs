"""Confluence document manager."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from html import escape
from importlib import import_module
from typing import Protocol, cast

from bs4 import BeautifulSoup
from bs4.element import Tag

from ss4d.config import Config
from ss4d.document.confluence_storage import split_h1_sections

STORY_POINTS = 1
STATUS_COLOURS = {
    "TODO": "Grey",
    "PROGRESS": "Blue",
    "REVIEW": "Red",
    "DONE": "Green",
}


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

    def sort_tasks(self) -> None:
        """Sort task sections in the configured Confluence page."""

        page = self.client.get_page_by_id(
            self.page_id,
            expand="body.storage,version",
        )
        self.client.update_page(
            self.page_id,
            _extract_page_title(page),
            sort_storage_body(_extract_storage_body(page)),
            representation="storage",
            minor_edit=False,
        )

    def update_task_status(self, number: int, status: str) -> None:
        """Update a task status in the configured Confluence page."""

        page = self.client.get_page_by_id(
            self.page_id,
            expand="body.storage,version",
        )
        self.client.update_page(
            self.page_id,
            _extract_page_title(page),
            update_storage_task_status(_extract_storage_body(page), number, status),
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
        f"{format_status_macro('TODO')}"
        "</h1>"
    )


def format_status_macro(status: str) -> str:
    """Format the Confluence storage status macro for a task status."""

    status_name = normalize_task_status(status)
    colour = STATUS_COLOURS[status_name]
    return (
        '<ac:structured-macro ac:name="status" ac:schema-version="1">'
        f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
        f'<ac:parameter ac:name="title">{status_name}</ac:parameter>'
        "</ac:structured-macro>"
    )


def sort_storage_body(body: str) -> str:
    """Sort h1 sections in a Confluence storage body by status and due date."""

    preamble, sections = split_h1_sections(body)
    sorted_sections = sorted(
        sections,
        key=lambda section: (section.is_done, section.due_date or date.max),
    )
    return f"{preamble}{''.join(section.body for section in sorted_sections)}"


def update_storage_task_status(body: str, number: int, status: str) -> str:
    """Update the status macro for a task h1 section in storage body."""

    status_macro = format_status_macro(status)
    preamble, sections = split_h1_sections(body)

    for index, section in enumerate(sections):
        if section.number != number:
            continue

        updated_section = _replace_section_status(section.body, status_macro)
        updated_sections = [
            other.body if section_index != index else updated_section
            for section_index, other in enumerate(sections)
        ]
        return f"{preamble}{''.join(updated_sections)}"

    raise RuntimeError(f"Task #{number} was not found.")


def normalize_task_status(status: str) -> str:
    """Return a supported uppercase status name."""

    status_name = status.upper()
    if status_name not in STATUS_COLOURS:
        allowed_statuses = ", ".join(STATUS_COLOURS)
        raise ValueError(f"Status must be one of: {allowed_statuses}.")
    return status_name


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


def _replace_section_status(section_body: str, status_macro: str) -> str:
    """Replace the first status macro in a section, or insert one in its h1."""

    soup = BeautifulSoup(section_body, "html.parser")
    h1 = soup.find("h1")
    if not isinstance(h1, Tag):
        raise RuntimeError("Task section did not include an h1 tag.")

    status_macro_tag = _parse_status_macro(status_macro)
    current_status_macro = h1.find(
        "ac:structured-macro",
        attrs={"ac:name": "status"},
    )
    if isinstance(current_status_macro, Tag):
        current_status_macro.replace_with(status_macro_tag)
        return str(soup)

    h1.append(" ")
    h1.append(status_macro_tag)
    return str(soup)


def _parse_status_macro(status_macro: str) -> Tag:
    """Parse a status macro fragment into a BeautifulSoup tag."""

    soup = BeautifulSoup(status_macro, "html.parser")
    macro = soup.find("ac:structured-macro", attrs={"ac:name": "status"})
    if not isinstance(macro, Tag):
        raise RuntimeError("Status macro fragment did not include a status macro.")
    return macro
