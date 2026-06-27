"""タスクポイント更新処理。"""

from dataclasses import replace
from pathlib import Path

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager
from ss4d.process.common.calculate_point import with_calculated_points

ALLOWED_POINTS = (1, 2, 3, 5, 8, 13, 21)


def update_task_point(
    number: int,
    point: int,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> int:
    """設定されたドキュメント内のタスクポイントを更新して返す。"""

    validate_point(point)
    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    sprint = document_manager.read_sprint()
    tasks = list(sprint.tasks)
    for index, task in enumerate(tasks):
        if task.id == number:
            tasks[index] = replace(task, points=point)
            document_manager.write_sprint(
                with_calculated_points(replace(sprint, tasks=tuple(tasks)))
            )
            return point

    raise RuntimeError(f"Task #{number} was not found.")


def validate_point(point: int) -> None:
    """タスクポイントが許可されたフィボナッチ数か検証する。"""

    if point not in ALLOWED_POINTS:
        allowed_points = ", ".join(str(allowed_point) for allowed_point in ALLOWED_POINTS)
        raise ValueError(f"Point must be one of: {allowed_points}.")
