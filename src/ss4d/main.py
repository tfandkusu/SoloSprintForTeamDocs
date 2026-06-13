"""Command-line interface for ss4d."""

import typer

from ss4d.config import ConfigError
from ss4d.process.add_task import create_task

app = typer.Typer(no_args_is_help=True)


@app.command()
def create(title: str) -> None:
    """Create a task heading in Confluence."""

    try:
        heading = create_task(title)
    except ConfigError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        typer.echo(f"Failed to create task: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(heading)


def main() -> None:
    app()
