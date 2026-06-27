from datetime import date
from typing import Any
from unittest import TestCase

from ss4d.document.confluence import ConfluenceDocumentManager
from ss4d.document.confluence_html_builder import (
    format_storage_sprint,
    format_storage_tasks,
)
from ss4d.document.confluence_html_parser import (
    parse_storage_sprint,
    parse_storage_tasks,
)
from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus


class FakeConfluenceClient:
    def __init__(self, *, page: dict[str, Any] | None = None) -> None:
        """ドキュメントマネージャーテスト用の偽 Confluence クライアントを作成する。"""

        self.page = page or {
            "title": "Sprint page",
            "body": {"storage": {"value": "<p>Existing</p>"}},
        }
        self.page_id: str | None = None
        self.expand: str | None = None
        self.updated_title: str | None = None
        self.updated_body: str | None = None
        self.representation: str | None = None
        self.minor_edit: bool | None = None

    def get_page_by_id(self, page_id: str, expand: str) -> dict[str, Any]:
        """取得リクエストを記録し、保存済みページレスポンスを返す。"""

        self.page_id = page_id
        self.expand = expand
        return self.page

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        *,
        representation: str,
        minor_edit: bool,
    ) -> object:
        """更新リクエストを記録する。"""

        self.page_id = page_id
        self.updated_title = title
        self.updated_body = body
        self.representation = representation
        self.minor_edit = minor_edit
        return object()


class ConfluenceDocumentManagerTest(TestCase):
    def test_read_sprint_converts_document_to_domain_model(self) -> None:
        """自由形式の HTML 本文を含むスプリント情報を読み込む。"""

        client = FakeConfluenceClient(
            page={
                "title": "Sprint page",
                "body": {
                    "storage": {
                        "value": (
                            "<p>Intro is not a task</p>"
                            "<h1>#2[3]Deploy &amp; verify "
                            '<time datetime="2026-06-30" /> '
                            f"{_status_macro('PROGRESS')}</h1>"
                            "<p>Keep this body</p>"
                        )
                    }
                },
            }
        )
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        self.assertEqual(
            manager.read_sprint(),
            Sprint(
                start_day=date.today(),
                done_point=0,
                remaining_point=3,
                all_point=3,
                tasks=(
                    Task(
                        id=2,
                        title="Deploy & verify",
                        points=3,
                        due_date=date(2026, 6, 30),
                        status=TaskStatus.PROGRESS,
                        body="<p>Keep this body</p>",
                    ),
                ),
            ),
        )
        self.assertEqual(client.page_id, "123")
        self.assertEqual(client.expand, "body.storage,version")

    def test_write_sprint_replaces_document_from_domain_model(self) -> None:
        """指定されたスプリントモデルを使ってドキュメント全体を置き換える。"""

        client = FakeConfluenceClient()
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        manager.write_sprint(
            Sprint(
                start_day=date(2026, 6, 14),
                done_point=99,
                remaining_point=99,
                all_point=99,
                tasks=(
                    Task(
                        id=1,
                        title="CI & deploy",
                        points=2,
                        due_date=None,
                        status=TaskStatus.REVIEW,
                        body="<p>Task body</p>",
                    ),
                ),
            )
        )

        self.assertEqual(client.updated_title, "Sprint page")
        self.assertEqual(
            client.updated_body,
            '<ac:structured-macro ac:name="code" ac:schema-version="1">'
            '<ac:parameter ac:name="language">toml</ac:parameter>'
            "<ac:plain-text-body><![CDATA["
            'start_day = "2026/06/14"\n'
            "done_point = 0\n"
            "remaining_point = 2\n"
            "all_point = 2\n"
            "]]></ac:plain-text-body>"
            "</ac:structured-macro>"
            "<h1>#1[2]CI &amp; deploy "
            '<ac:structured-macro ac:name="status" ac:schema-version="1">'
            '<ac:parameter ac:name="colour">Red</ac:parameter>'
            '<ac:parameter ac:name="title">REVIEW</ac:parameter>'
            "</ac:structured-macro></h1><p>Task body</p>",
        )
        self.assertEqual(client.representation, "storage")
        self.assertFalse(client.minor_edit)

    def test_storage_tasks_round_trip_all_domain_fields(self) -> None:
        """サポート対象のタスクフィールドを Confluence storage HTML 経由で往復させる。"""

        tasks = [
            Task(
                id=7,
                title="Escaped <title>",
                points=5,
                due_date=date(2026, 7, 1),
                status=TaskStatus.DONE,
                body="<p><strong>Finished</strong></p>",
            )
        ]

        self.assertEqual(parse_storage_tasks(format_storage_tasks(tasks)), tasks)

    def test_storage_sprint_round_trip_and_recalculates_points(self) -> None:
        """スプリント情報とタスク一覧を Confluence storage HTML 経由で往復させる。"""

        sprint = Sprint(
            start_day=date(2026, 6, 14),
            done_point=0,
            remaining_point=0,
            all_point=0,
            tasks=(
                Task(
                    id=7,
                    title="Finished",
                    points=5,
                    due_date=date(2026, 7, 1),
                    status=TaskStatus.DONE,
                    body="<p><strong>Finished</strong></p>",
                ),
                Task(
                    id=8,
                    title="Remaining",
                    points=4,
                    due_date=None,
                    status=TaskStatus.TODO,
                    body="",
                ),
            ),
        )

        self.assertEqual(
            parse_storage_sprint(format_storage_sprint(sprint)),
            Sprint(
                start_day=date(2026, 6, 14),
                done_point=5,
                remaining_point=4,
                all_point=9,
                tasks=sprint.tasks,
            ),
        )

    def test_read_sprint_converts_leading_toml_to_domain_model(self) -> None:
        """先頭 TOML コードブロックからスプリント情報を読み込む。"""

        client = FakeConfluenceClient(
            page={
                "title": "Sprint page",
                "body": {
                    "storage": {
                        "value": (
                            '<ac:structured-macro ac:name="code" '
                            'ac:schema-version="1">'
                            '<ac:parameter ac:name="language">toml</ac:parameter>'
                            "<ac:plain-text-body><![CDATA["
                            'start_day = "2026/06/14"\n'
                            "done_point = 1\n"
                            "remaining_point = 4\n"
                            "all_point = 2\n"
                            "]]></ac:plain-text-body>"
                            "</ac:structured-macro>"
                            f"<h1>#2[3]Deploy {_status_macro('DONE')}</h1>"
                        )
                    }
                },
            }
        )
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        self.assertEqual(
            manager.read_sprint(),
            Sprint(
                start_day=date(2026, 6, 14),
                done_point=1,
                remaining_point=4,
                all_point=2,
                tasks=(
                    Task(
                        id=2,
                        title="Deploy",
                        points=3,
                        due_date=None,
                        status=TaskStatus.DONE,
                        body="",
                    ),
                ),
            ),
        )

    def test_read_sprint_defaults_unknown_status_to_todo(self) -> None:
        """サポート外のドキュメントステータス名を todo タスクとして扱う。"""

        client = FakeConfluenceClient(
            page={
                "title": "Sprint page",
                "body": {
                    "storage": {
                        "value": (
                            f"<h1>#1[1]Blocked task {_status_macro('BLOCKED')}</h1>"
                        )
                    }
                },
            }
        )
        manager = ConfluenceDocumentManager(client=client, page_id="123")

        self.assertEqual(manager.read_sprint().tasks[0].status, TaskStatus.TODO)


def _status_macro(status: str) -> str:
    """ステータスマクロのフィクスチャを整形する。"""

    return (
        '<ac:structured-macro ac:name="status" ac:schema-version="1">'
        f'<ac:parameter ac:name="title">{status}</ac:parameter>'
        "</ac:structured-macro>"
    )
