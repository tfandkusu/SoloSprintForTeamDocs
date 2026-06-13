"""Create-task process."""

from datetime import date
from html import escape
from pathlib import Path

from ss4d.config import CONFIG_PATH, increment_number, load_config
from ss4d.document.manager import DocumentManager

STORY_POINTS = 1


def create_task(
    title: str,
    *,
    document_manager: DocumentManager,
    config_path: Path = CONFIG_PATH,
) -> int:
    """Append a task heading to Confluence and return the created task number."""

    config = load_config(config_path)
    task_number = config.number
    heading = format_task_heading(task_number, title)

    document_manager.append_heading(heading)

    increment_number(config_path)
    return task_number


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
