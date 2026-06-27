from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.update_task_due_date import parse_deadline, update_task_due_date


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """update-task-due-date テスト用の偽ドキュメントマネージャーを作成する。"""

        self.should_fail = should_fail
        self.sprint = Sprint(
            start_day=date(2026, 6, 14),
            done_point=99,
            all_point=99,
            tasks=[_task(7), _task(8, due_date=date(2026, 7, 1))],
        )
        self.write_count = 0

    def read_sprint(self) -> Sprint:
        """設定されたスプリントを返す。"""

        return self.sprint

    def write_sprint(self, sprint: Sprint) -> None:
        """置換後のスプリントを記録するか、設定された失敗を送出する。"""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.sprint = sprint
        self.write_count += 1


class UpdateTaskDueDateTest(TestCase):
    def test_parse_deadline_returns_iso_date(self) -> None:
        """日付表現を ISO 形式の日付へ解析する。"""

        self.assertEqual(parse_deadline("2026-06-30"), "2026-06-30")

    def test_update_task_due_date_replaces_only_matching_domain_model(self) -> None:
        """他のフィールドを維持しながら一致する期限日を更新する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            original_tasks = manager.sprint.tasks.copy()
            due_date = update_task_due_date(
                7,
                "2026-06-30",
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual(due_date, "2026-06-30")
        self.assertEqual(manager.sprint.tasks[0].due_date, date(2026, 6, 30))
        self.assertEqual(
            manager.sprint.tasks[0],
            replace(original_tasks[0], due_date=date(2026, 6, 30)),
        )
        self.assertEqual(manager.sprint.tasks[1], original_tasks[1])
        self.assertEqual(manager.sprint.start_day, date(2026, 6, 14))
        self.assertEqual(manager.sprint.done_point, 0)
        self.assertEqual(manager.sprint.all_point, 6)
        self.assertEqual(manager.write_count, 1)

    def test_unknown_deadline_does_not_update_document(self) -> None:
        """ドキュメントの読み書き前に未知の期限日を拒否する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(ValueError, "Could not parse deadline"):
                update_task_due_date(
                    7,
                    "",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_missing_task_does_not_update_document(self) -> None:
        """ドキュメントを書き込まずに存在しないタスク番号を拒否する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(RuntimeError, "Task #9 was not found"):
                update_task_due_date(
                    9,
                    "2026-06-30",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_failed_document_update_raises_error(self) -> None:
        """更新後タスクの書き込み失敗時にドキュメント更新エラーを送出する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(should_fail=True)
            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_due_date(
                    7,
                    "2026-06-30",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(number: int, *, due_date: date | None = None) -> Task:
    """更新で維持すべきフィールドを持つタスクフィクスチャを作成する。"""

    return Task(
        id=number,
        title=f"Task {number}",
        points=3,
        due_date=due_date,
        status=TaskStatus.REVIEW,
        body=f"<p>Body {number}</p>",
    )


def _write_config(directory: Path) -> Path:
    """テスト用の一時 ss4d 設定ファイルを書き込む。"""

    config_path = directory / ".ss4d.toml"
    config_path.write_text(
        'url = "https://example.atlassian.net/wiki"\n'
        'token = "token"\n'
        'page = "123"\n'
        'email = "user@example.com"\n'
        "number = 1\n",
        encoding="utf-8",
    )
    return config_path
