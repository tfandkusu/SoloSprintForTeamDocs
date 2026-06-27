"""ss4d のコマンドラインインターフェース。"""

import typer

from ss4d.config import ConfigError
from ss4d.process.create_task import create_task
from ss4d.process.sort_tasks import sort_tasks
from ss4d.process.update_task_due_date import update_task_due_date
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


def main() -> None:
    """Typer アプリケーションを実行する。"""

    app()
