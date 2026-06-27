from dataclasses import replace
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.update_task_point import update_task_point


class FakeDocumentManager:
    def __init__(
        self,
        *,
        should_fail: bool = False,
        target_status: TaskStatus = TaskStatus.REVIEW,
    ) -> None:
        """update-task-point テスト用の偽ドキュメントマネージャーを作成する。"""

        self.should_fail = should_fail
        self.sprint = Sprint(
            start_day=date(2026, 6, 14),
            done_point=99,
            remaining_point=99,
            all_point=99,
            tasks=(
                _task(7, points=3, status=target_status),
                _task(8, points=5, status=TaskStatus.PROGRESS),
            ),
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


class UpdateTaskPointTest(TestCase):
    def test_update_task_point_replaces_only_matching_domain_model(self) -> None:
        """他のタスクフィールドを維持しながら一致するポイントを更新する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            original_tasks = manager.sprint.tasks
            updated_point = update_task_point(
                7,
                4,
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual(updated_point, 4)
        self.assertEqual(manager.sprint.tasks[0].points, 4)
        self.assertEqual(
            manager.sprint.tasks[0],
            replace(original_tasks[0], points=4),
        )
        self.assertEqual(manager.sprint.tasks[1], original_tasks[1])
        self.assertEqual(manager.sprint.start_day, date(2026, 6, 14))
        self.assertEqual(manager.sprint.done_point, 0)
        self.assertEqual(manager.sprint.remaining_point, 9)
        self.assertEqual(manager.sprint.all_point, 9)
        self.assertEqual(manager.write_count, 1)

    def test_update_done_task_point_recalculates_done_points(self) -> None:
        """完了済みタスクのポイント更新で完了ポイントを再計算する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(target_status=TaskStatus.DONE)
            updated_point = update_task_point(
                7,
                13,
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual(updated_point, 13)
        self.assertEqual(manager.sprint.done_point, 13)
        self.assertEqual(manager.sprint.remaining_point, 5)
        self.assertEqual(manager.sprint.all_point, 18)
        self.assertEqual(manager.write_count, 1)

    def test_non_positive_point_does_not_update_document(self) -> None:
        """ドキュメントの読み書き前に自然数ではないポイントを拒否する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(ValueError, "Point must be 1 or greater"):
                update_task_point(
                    7,
                    0,
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_missing_task_does_not_update_document(self) -> None:
        """ドキュメントを書き込まずに存在しないタスク番号を拒否する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager()
            with self.assertRaisesRegex(RuntimeError, "Task #9 was not found"):
                update_task_point(
                    9,
                    8,
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )

        self.assertEqual(manager.write_count, 0)

    def test_failed_document_update_raises_error(self) -> None:
        """更新後タスクの書き込み失敗時にドキュメント更新エラーを送出する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(should_fail=True)
            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                update_task_point(
                    7,
                    8,
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(
    number: int,
    *,
    points: int,
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    """更新で維持すべきフィールドを持つタスクフィクスチャを作成する。"""

    return Task(
        id=number,
        title=f"Task {number}",
        points=points,
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
