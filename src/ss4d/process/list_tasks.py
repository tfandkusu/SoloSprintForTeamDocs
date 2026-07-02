"""タスク一覧取得処理。"""

from pathlib import Path

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


def list_tasks(
    *,
    show_all: bool = False,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> tuple[Task, ...]:
    """設定されたドキュメントから一覧表示対象のタスクを返す。"""

    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    tasks = document_manager.read_sprint().tasks
    if show_all:
        return tasks
    return tuple(task for task in tasks if task.status != TaskStatus.DONE)
