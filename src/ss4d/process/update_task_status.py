"""タスクステータス更新処理。"""

from dataclasses import replace
from pathlib import Path

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager
from ss4d.model.task_status import TaskStatus, normalize_task_status


def update_task_status(
    number: int,
    status: str,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> str:
    """設定されたドキュメント内のタスクステータスを更新して名前を返す。"""

    normalized_status = normalize_task_status(status)
    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    tasks = document_manager.read_tasks()
    for index, task in enumerate(tasks):
        if task.id == number:
            tasks[index] = replace(
                task,
                status=TaskStatus(normalized_status.lower()),
            )
            document_manager.write_tasks(tasks)
            return normalized_status

    raise RuntimeError(f"Task #{number} was not found.")
