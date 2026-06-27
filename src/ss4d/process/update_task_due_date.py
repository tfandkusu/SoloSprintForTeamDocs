"""タスク期限日更新処理。"""

from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime
from importlib import import_module
from pathlib import Path
from typing import cast

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import create_confluence_document_manager
from ss4d.document.manager import DocumentManager
from ss4d.process.common.calculate_point import with_calculated_points

DateParserParse = Callable[..., datetime | None]


def update_task_due_date(
    number: int,
    deadline: str,
    *,
    config_path: Path = CONFIG_PATH,
    document_manager: DocumentManager | None = None,
) -> str:
    """設定されたドキュメント内のタスク期限日を更新して返す。"""

    due_date = parse_deadline(deadline)
    config = load_config(config_path)

    if document_manager is None:
        document_manager = create_confluence_document_manager(config)

    sprint = document_manager.read_sprint()
    tasks = list(sprint.tasks)
    for index, task in enumerate(tasks):
        if task.id == number:
            tasks[index] = replace(task, due_date=date.fromisoformat(due_date))
            document_manager.write_sprint(
                with_calculated_points(replace(sprint, tasks=tuple(tasks)))
            )
            return due_date

    raise RuntimeError(f"Task #{number} was not found.")


def parse_deadline(deadline: str) -> str:
    """期限日の表現を解析して ISO 形式の日付を返す。"""

    dateparser = import_module("dateparser")
    parse = cast(DateParserParse, getattr(dateparser, "parse"))
    parsed_deadline = parse(deadline)
    if parsed_deadline is None:
        raise ValueError(f"Could not parse deadline: {deadline}")
    return parsed_deadline.date().isoformat()
