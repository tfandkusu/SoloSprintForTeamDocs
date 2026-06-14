"""Command-line interface for ss4d."""

import typer

from ss4d.config import ConfigError
from ss4d.process.create_task import create_task

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


def main() -> None:
    """Run the Typer application."""

    app()
