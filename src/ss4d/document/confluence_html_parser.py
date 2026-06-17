"""Confluence HTML body parser and serializer."""

import re
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup
from bs4.element import PageElement, Tag

from ss4d.document.confluence_html_builder import format_status_macro


@dataclass(frozen=True)
class H1Section:
    """An h1-led section from a Confluence HTML body."""

    body: str
    due_date: date | None
    is_done: bool
    number: int | None


def sort_storage_body(body: str) -> str:
    """Sort h1 sections in a Confluence HTML body by status and due date."""

    preamble, sections = split_h1_sections(body)
    sorted_sections = sorted(
        sections,
        key=lambda section: (section.is_done, section.due_date or date.max),
    )
    return f"{preamble}{''.join(section.body for section in sorted_sections)}"


def update_storage_task_status(body: str, number: int, status: str) -> str:
    """Update the status macro for a task h1 section in an HTML body."""

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


def split_h1_sections(body: str) -> tuple[str, list[H1Section]]:
    """Split an HTML body into a preamble and h1-led sections."""

    soup = BeautifulSoup(body, "html.parser")
    contents = list(soup.contents)
    h1_indexes = [
        index for index, element in enumerate(contents) if _is_tag(element, "h1")
    ]

    if len(h1_indexes) == 0:
        return str(soup), []

    preamble = _serialize(contents[: h1_indexes[0]])
    sections = [
        _create_section(contents[start:end])
        for start, end in zip(h1_indexes, [*h1_indexes[1:], len(contents)])
    ]
    return preamble, sections


def _create_section(elements: list[PageElement]) -> H1Section:
    """Create a sortable h1-led section from parsed elements."""

    h1 = elements[0]
    if not isinstance(h1, Tag):
        raise RuntimeError("Task section did not start with an h1 tag.")

    return H1Section(
        body=_serialize(elements),
        due_date=_extract_due_date(h1),
        is_done=_extract_status(h1).upper() == "DONE",
        number=_extract_task_number(h1),
    )


def _extract_due_date(h1: Tag) -> date | None:
    """Extract the first valid due date from an h1 tag."""

    time = h1.find("time")
    if not isinstance(time, Tag):
        return None

    raw_datetime = time.get("datetime")
    if not isinstance(raw_datetime, str):
        return None

    try:
        return date.fromisoformat(raw_datetime)
    except ValueError:
        return None


def _extract_status(h1: Tag) -> str:
    """Extract the first status macro title from an h1 tag."""

    status_macro = h1.find("ac:structured-macro", attrs={"ac:name": "status"})
    if not isinstance(status_macro, Tag):
        return ""

    title = status_macro.find("ac:parameter", attrs={"ac:name": "title"})
    if not isinstance(title, Tag):
        return ""

    return title.get_text(strip=True)


def _extract_task_number(h1: Tag) -> int | None:
    """Extract the first task number from an h1 tag."""

    match = re.search(r"#(\d+)(?!\d)", h1.get_text())
    if match is None:
        return None
    return int(match.group(1))


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


def _is_tag(element: PageElement, name: str) -> bool:
    """Return whether the element is a tag with the given name."""

    return isinstance(element, Tag) and element.name == name


def _serialize(elements: list[PageElement]) -> str:
    """Serialize parsed elements back to a storage-format fragment."""

    return "".join(str(element) for element in elements)
