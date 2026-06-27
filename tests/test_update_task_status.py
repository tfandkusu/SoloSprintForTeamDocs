from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.update_task_status import update_task_status


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """update-task-status テスト用の偽ドキュメントマネージャーを作成する。"""

        self.should_fail = should_fail
        self.sprint = Sprint(
            start_day=date(2026, 6, 14),
            done_point=99,
            all_point=99,
            tasks=(_task(7), _task(8, status=TaskStatus.PROGRESS)),
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


class UpdateTaskStatusTest(TestCase):
    def test_update_task_status_replaces_only_matching_domain_model(self) -> None:
        """他のタスクフィールドを維持しながら一致するステータスを更新する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            original_tasks = manager.sprint.tasks
            updated_status = update_task_status(
                7,
                "done",
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual(updated_status, "DONE")
        self.assertEqual(manager.sprint.tasks[0].status, TaskStatus.DONE)
        self.assertEqual(
            manager.sprint.tasks[0],
            replace(original_tasks[0], status=TaskStatus.DONE),
        )
        self.assertEqual(manager.sprint.tasks[1], original_tasks[1])
        self.assertEqual(manager.sprint.start_day, date(2026, 6, 14))
        self.assertEqual(manager.sprint.done_point, 3)
        self.assertEqual(manager.sprint.all_point, 6)
        self.assertEqual(manager.write_count, 1)

    def test_unknown_status_does_not_update_document(self) -> None:
        """ドキュメントの読み書き前に未知のステータスを拒否する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(ValueError, "Status must be one of"):
                update_task_status(
                    7,
                    "blocked",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_missing_task_does_not_update_document(self) -> None:
        """ドキュメントを書き込まずに存在しないタスク番号を拒否する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(RuntimeError, "Task #9 was not found"):
                update_task_status(
                    9,
                    "DONE",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_failed_document_update_raises_error(self) -> None:
        """更新後タスクの書き込み失敗時にドキュメント更新エラーを送出する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(should_fail=True)
            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_status(
                    7,
                    "DONE",
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(number: int, *, status: TaskStatus = TaskStatus.TODO) -> Task:
    """更新で維持すべきフィールドを持つタスクフィクスチャを作成する。"""

    return Task(
        id=number,
        title=f"Task {number}",
        points=3,
        due_date=date(2026, 6, 30),
        status=status,
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
