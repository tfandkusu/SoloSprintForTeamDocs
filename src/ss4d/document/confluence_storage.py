"""Confluence storage-format body parser."""

from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup
from bs4.element import PageElement, Tag


@dataclass(frozen=True)
class H1Section:
    """An h1-led section from a Confluence storage-format body."""

    body: str
    due_date: date | None
    is_done: bool


def split_h1_sections(body: str) -> tuple[str, list[H1Section]]:
    """Split a storage body into a preamble and h1-led sections."""

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


def _is_tag(element: PageElement, name: str) -> bool:
    """Return whether the element is a tag with the given name."""

    return isinstance(element, Tag) and element.name == name


def _serialize(elements: list[PageElement]) -> str:
    """Serialize parsed elements back to a storage-format fragment."""

    return "".join(str(element) for element in elements)
