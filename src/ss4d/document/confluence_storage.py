"""Confluence storage-format body parser."""

from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser


@dataclass(frozen=True)
class H1Section:
    """An h1-led section from a Confluence storage-format body."""

    body: str
    due_date: date | None
    is_done: bool


class H1StartParser(HTMLParser):
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


class DueDateParser(HTMLParser):
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


class StatusParser(HTMLParser):
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


def split_h1_sections(body: str) -> tuple[str, list[H1Section]]:
    """Split a storage body into a preamble and h1-led sections."""

    parser = H1StartParser()
    parser.feed(body)

    if len(parser.offsets) == 0:
        return body, []

    preamble = body[: parser.offsets[0]]
    sections: list[H1Section] = []
    section_offsets = [*parser.offsets, len(body)]

    for index, start_offset in enumerate(section_offsets[:-1]):
        section_body = body[start_offset : section_offsets[index + 1]]
        sections.append(
            H1Section(
                body=section_body,
                due_date=extract_due_date(section_body),
                is_done=extract_status(section_body).upper() == "DONE",
            )
        )

    return preamble, sections


def extract_due_date(section_body: str) -> date | None:
    """Extract the first valid due date from an h1 section."""

    parser = DueDateParser()
    parser.feed(section_body)
    return parser.due_date


def extract_status(section_body: str) -> str:
    """Extract the first status macro title from an h1 section."""

    parser = StatusParser()
    parser.feed(section_body)
    return parser.status or ""
