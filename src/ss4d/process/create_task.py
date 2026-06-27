"""タスク作成処理。"""

from dataclasses import replace
from datetime import date
from pathlib import Path

from ss4d.config import CONFIG_PATH, increment_number, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.common.calculate_point import with_calculated_points


def create_task(
    title: str,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> int:
    """設定されたドキュメントの先頭にタスクを追加して番号を返す。"""

    config = load_config(config_path)
    task_number = config.number

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    sprint = document_manager.read_sprint()
    tasks = list(sprint.tasks)
    tasks.insert(
        0,
        Task(
            id=task_number,
            title=title,
            points=1,
            due_date=date.today(),
            status=TaskStatus.TODO,
            body="",
        ),
    )
    document_manager.write_sprint(
        with_calculated_points(replace(sprint, tasks=tuple(tasks)))
    )

    increment_number(config_path)
    return task_number
