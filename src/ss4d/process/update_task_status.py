"""Update-task-status process."""

from pathlib import Path

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.confluence_html import normalize_task_status
from ss4d.document.manager import DocumentManager


def update_task_status(
    number: int,
    status: str,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> str:
    """Update a task status in the configured document and return its name."""

    normalized_status = normalize_task_status(status)
    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    document_manager.update_task_status(number, normalized_status)
    return normalized_status
