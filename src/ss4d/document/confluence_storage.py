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


@dataclass(frozen=True)
class _ParsedSection:
    """A parsed h1-led section before body slicing."""

    start_offset: int
    due_date: date | None
    status: str


@dataclass
class _SectionState:
    """Mutable parser state for the current h1-led section."""

    start_offset: int
    due_date: date | None = None
    status: str = ""


class _StorageBodyParser(HTMLParser):
    """Parse section boundaries and sortable metadata from a storage body."""

    def __init__(self) -> None:
        """Create a parser with no discovered sections."""

        super().__init__(convert_charrefs=False)
        self.sections: list[_ParsedSection] = []
        self._current_section: _SectionState | None = None
        self._inside_status_macro = False
        self._inside_title_parameter = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record section starts and sortable values from start tags."""

        lowered_tag = tag.lower()
        attr_values = dict(attrs)

        if lowered_tag == "h1":
            self._close_current_section()
            self._current_section = _SectionState(
                start_offset=self._get_starttag_text_offset()
            )
            return

        if self._current_section is None:
            return

        if lowered_tag == "time":
            self._record_due_date(attr_values.get("datetime"))
            return

        if lowered_tag == "ac:structured-macro":
            self._inside_status_macro = attr_values.get("ac:name") == "status"
            return

        if (
            self._inside_status_macro
            and lowered_tag == "ac:parameter"
            and attr_values.get("ac:name") == "title"
        ):
            self._inside_title_parameter = True
            self._title_parts = []

    def handle_data(self, data: str) -> None:
        """Collect status title text while inside a status macro title."""

        if self._inside_status_macro and self._inside_title_parameter:
            self._title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Record completed status titles and close macro state."""

        lowered_tag = tag.lower()
        if lowered_tag == "ac:parameter" and self._inside_title_parameter:
            self._record_status("".join(self._title_parts).strip())
            self._inside_title_parameter = False
            return

        if lowered_tag == "ac:structured-macro":
            self._inside_status_macro = False
            self._inside_title_parameter = False

    def close(self) -> None:
        """Close the parser and flush the final section."""

        super().close()
        self._close_current_section()

    def _close_current_section(self) -> None:
        """Append the current section to parsed sections."""

        if self._current_section is None:
            return

        self.sections.append(
            _ParsedSection(
                start_offset=self._current_section.start_offset,
                due_date=self._current_section.due_date,
                status=self._current_section.status,
            )
        )
        self._current_section = None
        self._inside_status_macro = False
        self._inside_title_parameter = False

    def _get_starttag_text_offset(self) -> int:
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

    def _record_due_date(self, raw_datetime: str | None) -> None:
        """Record the first valid due date for the current section."""

        if self._current_section is None or self._current_section.due_date is not None:
            return

        if raw_datetime is None:
            return

        try:
            self._current_section.due_date = date.fromisoformat(raw_datetime)
        except ValueError:
            return

    def _record_status(self, status: str) -> None:
        """Record the first status title for the current section."""

        if self._current_section is None or self._current_section.status != "":
            return

        self._current_section.status = status


def split_h1_sections(body: str) -> tuple[str, list[H1Section]]:
    """Split a storage body into a preamble and h1-led sections."""

    parser = _StorageBodyParser()
    parser.feed(body)
    parser.close()

    if len(parser.sections) == 0:
        return body, []

    preamble = body[: parser.sections[0].start_offset]
    sections: list[H1Section] = []
    section_offsets = [section.start_offset for section in parser.sections]

    for index, section in enumerate(parser.sections):
        end_offset = (
            section_offsets[index + 1]
            if index + 1 < len(section_offsets)
            else len(body)
        )
        sections.append(
            H1Section(
                body=body[section.start_offset : end_offset],
                due_date=section.due_date,
                is_done=section.status.upper() == "DONE",
            )
        )

    return preamble, sections
