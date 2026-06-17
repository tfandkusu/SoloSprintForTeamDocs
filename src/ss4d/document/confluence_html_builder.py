"""Confluence HTML fragment builder."""

from datetime import date
from html import escape

from ss4d.document.confluence_html_parser import (
    replace_section_status,
    split_h1_sections,
)

STORY_POINTS = 1
STATUS_COLOURS = {
    "TODO": "Grey",
    "PROGRESS": "Blue",
    "REVIEW": "Red",
    "DONE": "Green",
}


def format_task_heading(
    number: int, title: str, *, due_date: date | None = None
) -> str:
    """Format the Confluence HTML h1 for a task."""

    task_due_date = due_date or date.today()
    return (
        f"<h1>#{number}[{STORY_POINTS}]{escape(title)} "
        f'<time datetime="{task_due_date.isoformat()}" /> '
        f"{format_status_macro('TODO')}"
        "</h1>"
    )


def format_status_macro(status: str) -> str:
    """Format the Confluence HTML status macro for a task status."""

    status_name = normalize_task_status(status)
    colour = STATUS_COLOURS[status_name]
    return (
        '<ac:structured-macro ac:name="status" ac:schema-version="1">'
        f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
        f'<ac:parameter ac:name="title">{status_name}</ac:parameter>'
        "</ac:structured-macro>"
    )


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

        updated_section = replace_section_status(section.body, status_macro)
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
