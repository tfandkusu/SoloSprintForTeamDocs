from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.sort_tasks import sort_tasks


class FakeDocumentManager:
    def __init__(self, tasks: list[Task], *, should_fail: bool = False) -> None:
        """sort-task テスト用の偽ドキュメントマネージャーを作成する。"""

        self.sprint = Sprint(
            start_day=date(2026, 6, 14),
            done_point=99,
            all_point=99,
            tasks=tuple(tasks),
        )
        self.should_fail = should_fail
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


class SortTasksTest(TestCase):
    def test_sort_tasks_updates_domain_models_by_status_and_due_date(self) -> None:
        """未完了タスクを完了タスクより前に置き、期限日なしを最後に並べる。"""

        tasks = [
            _task(1, due_date=date(2026, 6, 20)),
            _task(2, due_date=None),
            _task(3, due_date=date(2026, 6, 18)),
            _task(4, due_date=date(2026, 6, 18)),
            _task(5, due_date=date(2026, 6, 10), status=TaskStatus.DONE),
        ]

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager(tasks)
            sort_tasks(
                config_path=_write_config(Path(directory)),
                document_manager=manager,
            )

        self.assertEqual([task.id for task in manager.sprint.tasks], [3, 4, 1, 2, 5])
        self.assertEqual(manager.sprint.start_day, date(2026, 6, 14))
        self.assertEqual(manager.sprint.done_point, 5)
        self.assertEqual(manager.sprint.all_point, 15)
        self.assertEqual(manager.write_count, 1)

    def test_failed_document_update_raises_error(self) -> None:
        """並び替え後タスクの書き込み失敗時にドキュメント更新エラーを送出する。"""

        with TemporaryDirectory() as directory:
            manager = FakeDocumentManager([_task(1)], should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                sort_tasks(
                    config_path=_write_config(Path(directory)),
                    document_manager=manager,
                )


def _task(
    number: int,
    *,
    due_date: date | None = None,
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    """並び替え可能なフィールドを持つタスクフィクスチャを作成する。"""

    return Task(
        id=number,
        title=f"Task {number}",
        points=number,
        due_date=due_date,
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
