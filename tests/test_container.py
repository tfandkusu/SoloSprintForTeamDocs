from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.container import Container
from ss4d.document.confluence import ConfluenceDocumentManager
from ss4d.document.manager import DocumentManager


class ContainerTest(TestCase):
    def test_document_manager_resolves_to_confluence_implementation(self) -> None:
        """Resolve the configured document manager implementation."""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                'page = "123"\n'
                'email = "user@example.com"\n'
                "number = 1\n",
                encoding="utf-8",
            )
            container = Container(config_path=config_path)
            container.confluence_client.override(object())

            document_manager = container.document_manager()

        self.assertIsInstance(document_manager, ConfluenceDocumentManager)
        self.assertIsInstance(document_manager, DocumentManager)
