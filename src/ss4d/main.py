"""Command-line interface for ss4d."""

import typer

from ss4d.config import ConfigError
from ss4d.process.create_task import create_task
from ss4d.process.sort_tasks import sort_tasks
from ss4d.process.update_task_status import update_task_status

app = typer.Typer(no_args_is_help=True)


@app.callback()
def callback() -> None:
    """SoloSprintForTeamDocs command-line tool."""


@app.command()
def create(title: str) -> None:
    """Create a task heading in Confluence."""

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
    """Sort task headings in Confluence."""

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
    """Update a task status in Confluence."""

    try:
        updated_status = update_task_status(number, status_name)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to update task status: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Updated task #{number} to {updated_status}")


def main() -> None:
    """Run the Typer application."""

    app()
