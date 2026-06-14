"""Create-task process."""

from pathlib import Path

from ss4d.config import CONFIG_PATH, increment_number, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager


def create_task(
    title: str,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> int:
    """Append a task to the configured document and return the task number."""

    config = load_config(config_path)
    task_number = config.number

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    document_manager.append_task(task_number, title)

    increment_number(config_path)
    return task_number
