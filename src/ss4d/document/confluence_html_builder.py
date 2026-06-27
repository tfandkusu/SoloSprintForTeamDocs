"""Confluence HTML フラグメントビルダー。"""

from html import escape

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import normalize_task_status
from ss4d.process.common.calculate_point import with_calculated_points

STATUS_COLOURS = {
    "TODO": "Grey",
    "PROGRESS": "Blue",
    "REVIEW": "Red",
    "DONE": "Green",
}


def format_storage_sprint(sprint: Sprint) -> str:
    """スプリントを Confluence storage 形式の本文へシリアライズする。"""

    calculated_sprint = with_calculated_points(sprint)
    return (
        f"{_format_sprint_info(calculated_sprint)}"
        f"{format_storage_tasks(calculated_sprint.tasks)}"
    )


def format_storage_tasks(tasks: list[Task]) -> str:
    """タスクを Confluence storage 形式の本文へシリアライズする。"""

    return "".join(f"{_format_task(task)}{task.body}" for task in tasks)


def _format_sprint_info(sprint: Sprint) -> str:
    """スプリント情報を TOML の Confluence code macro として整形する。"""

    raw_toml = (
        f'start_day = "{sprint.start_day.strftime("%Y/%m/%d")}"\n'
        f"done_point = {sprint.done_point}\n"
        f"all_point = {sprint.all_point}\n"
    )
    return (
        '<ac:structured-macro ac:name="code" ac:schema-version="1">'
        '<ac:parameter ac:name="language">toml</ac:parameter>'
        f"<ac:plain-text-body><![CDATA[{raw_toml}]]></ac:plain-text-body>"
        "</ac:structured-macro>"
    )


def _format_task(task: Task) -> str:
    """すべてのドメインモデルフィールドを使ってタスク見出し 1 件を整形する。"""

    due_date = (
        f' <time datetime="{task.due_date.isoformat()}" />'
        if task.due_date is not None
        else ""
    )
    return (
        f"<h1>#{task.id}[{task.points}]{escape(task.title)}"
        f"{due_date} {format_status_macro(task.status.value)}</h1>"
    )


def format_status_macro(status: str) -> str:
    """タスクステータス用の Confluence HTML ステータスマクロを整形する。"""

    status_name = normalize_task_status(status)
    colour = STATUS_COLOURS[status_name]
    return (
        '<ac:structured-macro ac:name="status" ac:schema-version="1">'
        f'<ac:parameter ac:name="colour">{colour}</ac:parameter>'
        f'<ac:parameter ac:name="title">{status_name}</ac:parameter>'
        "</ac:structured-macro>"
    )
