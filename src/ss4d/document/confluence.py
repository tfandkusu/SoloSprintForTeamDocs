"""Confluence document manager."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from html import escape
from html.parser import HTMLParser
from importlib import import_module
from typing import Protocol, cast

from ss4d.config import Config

STORY_POINTS = 1
STATUS_COLOURS = {
    "TODO": "Grey",
    "PROGRESS": "Blue",
    "REVIEW": "Red",
    "DONE": "Green",
}
_STATUS_MACRO_PATTERN = re.compile(
    r'<ac:structured-macro\b(?=[^>]*\bac:name="status")[\s\S]*?</ac:structured-macro>'
)


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

    preamble, sections = _split_h1_sections(body)
    sorted_sections = sorted(
        sections,
        key=lambda section: (section.is_done, section.due_date or date.max),
    )
    return f"{preamble}{''.join(section.body for section in sorted_sections)}"


def update_storage_task_status(body: str, number: int, status: str) -> str:
    """Update the status macro for a task h1 section in storage body."""

    status_macro = format_status_macro(status)
    preamble, sections = _split_h1_sections(body)

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


@dataclass(frozen=True)
class _H1Section:
    """A sortable h1-led section from a storage-format body."""

    body: str
    due_date: date | None
    is_done: bool
    number: int | None


class _H1StartParser(HTMLParser):
    """Find h1 start-tag offsets in a storage-format body."""

    def __init__(self) -> None:
        """Create a parser with no discovered offsets."""

        super().__init__(convert_charrefs=False)
        self.offsets: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record h1 start-tag offsets."""

        if tag.lower() == "h1":
            self.offsets.append(self.get_starttag_text_offset())

    def get_starttag_text_offset(self) -> int:
        """Return the absolute offset for the current start tag."""

        line_number, column_number = self.getpos()
        line_starts = self._line_starts
        return line_starts[line_number - 1] + column_number

    @property
    def _line_starts(self) -> list[int]:
        """Return absolute offsets for every line start."""

        line_starts = [0]
        for index, character in enumerate(self.rawdata):
            if character == "\n":
                line_starts.append(index + 1)
        return line_starts


class _DueDateParser(HTMLParser):
    """Find the first time datetime value in an h1 section."""

    def __init__(self) -> None:
        """Create a parser with no discovered due date."""

        super().__init__(convert_charrefs=False)
        self.due_date: date | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record the first valid time datetime value."""

        if tag.lower() != "time" or self.due_date is not None:
            return

        raw_datetime = dict(attrs).get("datetime")
        if raw_datetime is None:
            return

        try:
            self.due_date = date.fromisoformat(raw_datetime)
        except ValueError:
            return


class _TaskHeadingParser(HTMLParser):
    """Find task metadata in an h1 section."""

    def __init__(self) -> None:
        """Create a parser with no discovered task metadata."""

        super().__init__(convert_charrefs=False)
        self.number: int | None = None
        self.status = ""
        self._h1_depth = 0
        self._status_macro_depth = 0
        self._in_status_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record h1 nesting and status macro parameter state."""

        attributes = dict(attrs)
        tag_name = tag.lower()
        if tag_name == "h1":
            self._h1_depth += 1

        if self._h1_depth == 0:
            return

        if tag_name == "ac:structured-macro" and attributes.get("ac:name") == "status":
            self._status_macro_depth += 1
            return

        if (
            self._status_macro_depth > 0
            and tag_name == "ac:parameter"
            and attributes.get("ac:name") == "title"
        ):
            self._in_status_title = True

    def handle_endtag(self, tag: str) -> None:
        """Record h1 nesting and status macro parameter state."""

        tag_name = tag.lower()
        if tag_name == "ac:parameter":
            self._in_status_title = False
            return

        if tag_name == "ac:structured-macro" and self._status_macro_depth > 0:
            self._status_macro_depth -= 1
            return

        if tag_name == "h1" and self._h1_depth > 0:
            self._h1_depth -= 1

    def handle_data(self, data: str) -> None:
        """Record task number and status title found in heading text."""

        if self._h1_depth == 0:
            return

        if self.number is None:
            match = re.search(r"#(\d+)(?!\d)", data)
            if match is not None:
                self.number = int(match.group(1))

        if self._in_status_title and self.status == "":
            self.status = data.strip()


def _split_h1_sections(body: str) -> tuple[str, list[_H1Section]]:
    """Split a storage body into a preamble and h1-led sections."""

    parser = _H1StartParser()
    parser.feed(body)

    if len(parser.offsets) == 0:
        return body, []

    preamble = body[: parser.offsets[0]]
    sections: list[_H1Section] = []
    section_offsets = [*parser.offsets, len(body)]

    for index, start_offset in enumerate(section_offsets[:-1]):
        section_body = body[start_offset : section_offsets[index + 1]]
        sections.append(
            _H1Section(
                body=section_body,
                due_date=_extract_due_date(section_body),
                is_done=_extract_task_status(section_body).upper() == "DONE",
                number=_extract_task_number(section_body),
            )
        )

    return preamble, sections


def _extract_due_date(section_body: str) -> date | None:
    """Extract the first valid due date from an h1 section."""

    parser = _DueDateParser()
    parser.feed(section_body)
    return parser.due_date


def _extract_task_number(section_body: str) -> int | None:
    """Extract the first task number from an h1 section."""

    parser = _TaskHeadingParser()
    parser.feed(section_body)
    return parser.number


def _extract_task_status(section_body: str) -> str:
    """Extract the first task status from an h1 section."""

    parser = _TaskHeadingParser()
    parser.feed(section_body)
    return parser.status


def _replace_section_status(section_body: str, status_macro: str) -> str:
    """Replace the first status macro in a section, or insert one in its h1."""

    updated_body, replacements = _STATUS_MACRO_PATTERN.subn(
        status_macro,
        section_body,
        count=1,
    )
    if replacements > 0:
        return updated_body

    h1_end = section_body.lower().find("</h1>")
    if h1_end == -1:
        raise RuntimeError("Task heading did not include a closing h1 tag.")

    return f"{section_body[:h1_end]} {status_macro}{section_body[h1_end:]}"
