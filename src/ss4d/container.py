"""Dependency injection container for ss4d."""

from dependency_injector import containers, providers

from ss4d.config import CONFIG_PATH, load_config
from ss4d.document.confluence import (
    ConfluenceDocumentManager,
    create_confluence_client,
)
from ss4d.process.create_task import create_task


class Container(containers.DeclarativeContainer):
    """Application dependency container."""

    config_path = providers.Object(CONFIG_PATH)
    config = providers.Callable(load_config, path=config_path)

    confluence_client = providers.Callable(create_confluence_client, config=config)
    document_manager = providers.Factory(
        ConfluenceDocumentManager,
        client=confluence_client,
        page_id=config.provided.page,
    )

    create_task = providers.Callable(
        create_task,
        config_path=config_path,
        document_manager=document_manager,
    )
