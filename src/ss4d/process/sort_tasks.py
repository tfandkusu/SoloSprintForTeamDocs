"""タスク並び替え処理。"""

from datetime import date
from pathlib import Path

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager
from ss4d.model.task_status import TaskStatus


def sort_tasks(
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> None:
    """設定されたドキュメント内のタスクセクションを並び替える。"""

    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    tasks = document_manager.read_tasks()
    tasks.sort(
        key=lambda task: (
            task.status == TaskStatus.DONE,
            task.due_date or date.max,
        )
    )
    document_manager.write_tasks(tasks)
