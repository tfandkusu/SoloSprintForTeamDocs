"""Confluence document manager."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from html import escape
from html.parser import HTMLParser
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


def sort_storage_body(body: str) -> str:
    """Sort h1 sections in a Confluence storage body by status and due date."""

    preamble, sections = _split_h1_sections(body)
    sorted_sections = sorted(
        sections,
        key=lambda section: (section.is_done, section.due_date or date.max),
    )
    return f"{preamble}{''.join(section.body for section in sorted_sections)}"


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


class _StatusParser(HTMLParser):
    """Find the first task status macro title in an h1 section."""

    def __init__(self) -> None:
        """Create a parser with no discovered status."""

        super().__init__(convert_charrefs=False)
        self.status: str | None = None
        self._inside_status_macro = False
        self._inside_title_parameter = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track status macro and title parameter start tags."""

        if self.status is not None:
            return

        attr_values = dict(attrs)
        if tag.lower() == "ac:structured-macro":
            self._inside_status_macro = attr_values.get("ac:name") == "status"
            return

        if not self._inside_status_macro or tag.lower() != "ac:parameter":
            return

        if attr_values.get("ac:name") == "title":
            self._inside_title_parameter = True
            self._title_parts = []

    def handle_data(self, data: str) -> None:
        """Collect title parameter text while inside a status macro."""

        if self._inside_status_macro and self._inside_title_parameter:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Track status macro and title parameter end tags."""

        lowered_tag = tag.lower()
        if lowered_tag == "ac:parameter" and self._inside_title_parameter:
            self.status = "".join(self._title_parts).strip()
            self._inside_title_parameter = False
            return

        if lowered_tag == "ac:structured-macro":
            self._inside_status_macro = False
            self._inside_title_parameter = False


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
                is_done=_extract_status(section_body).upper() == "DONE",
            )
        )

    return preamble, sections


def _extract_due_date(section_body: str) -> date | None:
    """Extract the first valid due date from an h1 section."""

    parser = _DueDateParser()
    parser.feed(section_body)
    return parser.due_date


def _extract_status(section_body: str) -> str:
    """Extract the first status macro title from an h1 section."""

    parser = _StatusParser()
    parser.feed(section_body)
    return parser.status or ""
