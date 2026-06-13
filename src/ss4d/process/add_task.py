"""Add-task process."""

from collections.abc import Callable, Mapping
from html import escape
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

from ss4d.config import CONFIG_PATH, Config, increment_number, load_config

STORY_POINTS = 1


class ConfluenceClient(Protocol):
    """Small subset of ConfluenceCloud used by this process."""

    def get_page_by_id(self, page_id: str, expand: str) -> Mapping[str, object]:
        """Fetch a Confluence page."""
        ...

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        *,
        representation: str,
        minor_edit: bool,
    ) -> object:
        """Update a Confluence page."""
        ...


type ConfluenceClientFactory = Callable[[Config], ConfluenceClient]


def create_task(
    title: str,
    *,
    config_path: Path = CONFIG_PATH,
    client_factory: ConfluenceClientFactory | None = None,
) -> str:
    """Append a task heading to Confluence and increment the task number."""

    if client_factory is None:
        client_factory = _create_confluence_client

    config = load_config(config_path)
    heading = format_task_heading(config.number, title)

    client = client_factory(config)
    page = client.get_page_by_id(
        config.page,
        expand="body.storage,version",
    )
    client.update_page(
        config.page,
        _extract_page_title(page),
        _append_storage_body(page, heading),
        representation="storage",
        minor_edit=False,
    )

    increment_number(config_path)
    return heading


def format_task_heading(number: int, title: str) -> str:
    """Format the Confluence storage h1 for a task."""

    return f"<h1>#{number}[{STORY_POINTS}]{escape(title)}</h1>"


def _create_confluence_client(config: Config) -> ConfluenceClient:
    confluence_module = import_module("atlassian")
    confluence = getattr(confluence_module, "Confluence")
    return cast(
        ConfluenceClient,
        confluence(url=config.url, token=config.token, cloud=True),
    )


def _append_storage_body(page: Mapping[str, object], heading: str) -> str:
    current_body = _extract_storage_body(page)
    return f"{current_body}{heading}"


def _extract_page_title(page: Mapping[str, object]) -> str:
    title = page.get("title")
    if not isinstance(title, str) or title == "":
        raise RuntimeError("Confluence page response did not include a title.")
    return title


def _extract_storage_body(page: Mapping[str, object]) -> str:
    body = page.get("body")
    if not isinstance(body, Mapping):
        return ""

    typed_body = cast(Mapping[str, object], body)
    storage = typed_body.get("storage")
    if not isinstance(storage, Mapping):
        return ""

    typed_storage = cast(Mapping[str, object], storage)
    value = typed_storage.get("value")
    if not isinstance(value, str):
        return ""

    return value
