"""Sort-task process."""

from pathlib import Path

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager


def sort_tasks(
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> None:
    """Sort task sections in the configured document."""

    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    document_manager.sort_tasks()
