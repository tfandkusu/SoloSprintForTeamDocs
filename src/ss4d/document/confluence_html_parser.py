"""Confluence HTML body parser and serializer."""

import re
from datetime import date

from bs4 import BeautifulSoup
from bs4.element import PageElement, Tag

from ss4d.document.confluence_h1_section import H1Section
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


def parse_storage_tasks(body: str) -> list[Task]:
    """Parse task sections from a Confluence storage-format body."""

    _, sections = split_h1_sections(body)
    return [_parse_task(section.body) for section in sections]


def _parse_task(section_body: str) -> Task:
    """Parse one h1-led storage-format section into a task."""

    soup = BeautifulSoup(section_body, "html.parser")
    h1 = soup.find("h1")
    if not isinstance(h1, Tag):
        raise RuntimeError("Task section did not include an h1 tag.")

    number = _extract_task_number(h1)
    if number is None:
        raise RuntimeError("Task heading did not include a task number.")

    points_match = re.search(r"#\d+\[(\d+)\]", h1.get_text())
    points = int(points_match.group(1)) if points_match is not None else 1
    status_name = _extract_status(h1).lower() or TaskStatus.TODO.value
    try:
        status = TaskStatus(status_name)
    except ValueError as error:
        raise RuntimeError(f"Unsupported task status: {status_name}.") from error

    heading = BeautifulSoup(str(h1), "html.parser").find("h1")
    if not isinstance(heading, Tag):
        raise RuntimeError("Task section did not include an h1 tag.")
    for element in heading.find_all(
        ["time", "ac:structured-macro"],
    ):
        element.decompose()
    title = re.sub(r"^#\d+(?:\[\d+\])?", "", heading.get_text()).strip()

    section_elements = list(soup.contents)
    return Task(
        id=number,
        title=title,
        points=points,
        due_date=_extract_due_date(h1),
        status=status,
        body=_serialize(section_elements[1:]),
    )


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


def _is_tag(element: PageElement, name: str) -> bool:
    """Return whether the element is a tag with the given name."""

    return isinstance(element, Tag) and element.name == name


def _serialize(elements: list[PageElement]) -> str:
    """Serialize parsed elements back to a storage-format fragment."""

    return "".join(str(element) for element in elements)
