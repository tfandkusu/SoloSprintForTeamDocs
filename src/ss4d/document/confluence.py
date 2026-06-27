"""Confluence ドキュメントマネージャー。"""

from collections.abc import Mapping
from dataclasses import dataclass
from importlib import import_module
from typing import Protocol, cast

from ss4d.config import Config
from ss4d.document.confluence_html_builder import format_storage_sprint
from ss4d.document.confluence_html_parser import parse_storage_sprint
from ss4d.model.sprint import Sprint


class ConfluenceClient(Protocol):
    """ドキュメントマネージャーが使う ConfluenceCloud の小さなサブセット。"""

    def get_page_by_id(self, page_id: str, expand: str) -> Mapping[str, object]:
        """Confluence ページを取得する。"""
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
        """Confluence ページを更新する。"""
        ...


@dataclass(frozen=True)
class ConfluenceDocumentManager:
    """Confluence をバックエンドにするドキュメントマネージャー実装。"""

    client: ConfluenceClient
    page_id: str

    def read_sprint(self) -> Sprint:
        """設定された Confluence ページからスプリント情報を読み込む。"""

        page = self.client.get_page_by_id(
            self.page_id,
            expand="body.storage,version",
        )
        return parse_storage_sprint(_extract_storage_body(page))

    def write_sprint(self, sprint: Sprint) -> None:
        """指定されたスプリント情報で設定済みの Confluence ページを上書きする。"""

        page = self.client.get_page_by_id(
            self.page_id,
            expand="body.storage,version",
        )
        self.client.update_page(
            self.page_id,
            _extract_page_title(page),
            format_storage_sprint(sprint),
            representation="storage",
            minor_edit=False,
        )


def create_confluence_document_manager(config: Config) -> ConfluenceDocumentManager:
    """設定から Confluence ドキュメントマネージャーを作成する。"""

    return ConfluenceDocumentManager(
        client=create_confluence_client(config),
        page_id=config.page,
    )


def create_confluence_client(config: Config) -> ConfluenceClient:
    """設定から認証済み Confluence クライアントを作成する。"""

    confluence_module = import_module("atlassian")
    confluence = getattr(confluence_module, "Confluence")
    return cast(
        ConfluenceClient,
        confluence(
            url=config.url,
            username=config.email,
            password=config.token,
            cloud=True,
        ),
    )


def _extract_page_title(page: Mapping[str, object]) -> str:
    """API レスポンスから Confluence ページタイトルを抽出する。"""

    title = page.get("title")
    if not isinstance(title, str) or title == "":
        raise RuntimeError("Confluence page response did not include a title.")
    return title


def _extract_storage_body(page: Mapping[str, object]) -> str:
    """API レスポンスから storage 形式の本文を抽出する。"""

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
