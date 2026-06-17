"""Update-task-due-date process."""

from collections.abc import Callable
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import cast

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager

DateParserParse = Callable[..., datetime | None]


def update_task_due_date(
    number: int,
    deadline: str,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> str:
    """Update a task due date in the configured document and return it."""

    due_date = parse_deadline(deadline)
    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    document_manager.update_task_due_date(number, due_date)
    return due_date


def parse_deadline(deadline: str) -> str:
    """Parse a deadline expression and return an ISO date."""

    dateparser = import_module("dateparser")
    parse = cast(DateParserParse, getattr(dateparser, "parse"))
    parsed_deadline = parse(deadline)
    if parsed_deadline is None:
        raise ValueError(f"Could not parse deadline: {deadline}")
    return parsed_deadline.date().isoformat()
