"""ss4d のコマンドラインインターフェース。"""

from typing import Annotated

import typer

from ss4d.config import ConfigError
from ss4d.format import format_task_lines
from ss4d.process.create_task import create_task
from ss4d.process.list_tasks import list_tasks
from ss4d.process.sort_tasks import sort_tasks
from ss4d.process.update_task_due_date import update_task_due_date
from ss4d.process.update_task_point import update_task_point
from ss4d.process.update_task_status import update_task_status

app = typer.Typer(no_args_is_help=True)


@app.callback()
def callback() -> None:
    """SoloSprintForTeamDocs のコマンドラインツール。"""


@app.command()
def create(title: str) -> None:
    """Confluence にタスク見出しを作成する。"""

    try:
        task_number = create_task(title)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to create task: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Created task #{task_number}")


@app.command()
def sort() -> None:
    """Confluence のタスク見出しを並び替える。"""

    try:
        sort_tasks()
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to sort tasks: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("Sorted tasks")


@app.command()
def status(number: int, status_name: str) -> None:
    """Confluence のタスクステータスを更新する。"""

    try:
        updated_status = update_task_status(number, status_name)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to update task status: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Updated task #{number} to {updated_status}")


@app.command()
def due(number: int, deadline: str) -> None:
    """Confluence のタスク期限日を更新する。"""

    try:
        due_date = update_task_due_date(number, deadline)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to update task due date: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Updated task #{number} due date to {due_date}")


@app.command()
def point(number: int, point: int) -> None:
    """Confluence のタスクポイントを更新する。"""

    try:
        updated_point = update_task_point(number, point)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to update task point: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Updated task #{number} point to {updated_point}")


@app.command("list")
def list_command(
    scope: Annotated[str, typer.Argument()] = "remaining",
) -> None:
    """Confluence のタスク一覧を表示する。"""

    try:
        show_all = _parse_list_scope(scope)
        tasks = list_tasks(show_all=show_all)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to list tasks: {error}", err=True)
        raise typer.Exit(code=1) from error

    if not tasks:
        typer.echo("No tasks found")
        return

    for line in format_task_lines(tasks):
        typer.echo(line)


def main() -> None:
    """Typer アプリケーションを実行する。"""

    app()


def _parse_list_scope(scope: str) -> bool:
    """list コマンドの表示対象を解釈して全件表示かどうかを返す。"""

    normalized_scope = scope.lower()
    if normalized_scope == "remaining":
        return False
    if normalized_scope == "all":
        return True
    raise ValueError("List scope must be either 'remaining' or 'all'.")
