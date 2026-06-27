from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.create_task import create_task


class FakeDocumentManager:
    def __init__(self, *, should_fail: bool = False) -> None:
        """create-task テスト用の偽ドキュメントマネージャーを作成する。"""

        self.should_fail = should_fail
        self.sprint = Sprint(
            start_day=date(2026, 6, 14),
            done_point=99,
            all_point=99,
            tasks=(
                Task(
                    id=2,
                    title="Existing",
                    points=3,
                    due_date=None,
                    status=TaskStatus.PROGRESS,
                    body="<p>Existing body</p>",
                ),
            ),
        )

    def read_sprint(self) -> Sprint:
        """設定されたスプリントを返す。"""

        return self.sprint

    def write_sprint(self, sprint: Sprint) -> None:
        """置換後のスプリントを記録するか、設定された失敗を送出する。"""

        if self.should_fail:
            raise RuntimeError("Document update failed")
        self.sprint = sprint


class CreateTaskTest(TestCase):
    def test_create_task_updates_document_and_increments_number(self) -> None:
        """ドキュメントを更新し、成功後にタスク番号をインクリメントする。"""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager()

            task_number = create_task(
                "CI setup",
                config_path=config_path,
                document_manager=document_manager,
            )

            self.assertEqual(task_number, 1)
            self.assertEqual(
                document_manager.sprint,
                Sprint(
                    start_day=date(2026, 6, 14),
                    done_point=0,
                    all_point=4,
                    tasks=(
                        Task(
                            id=1,
                            title="CI setup",
                            points=1,
                            due_date=date.today(),
                            status=TaskStatus.TODO,
                            body="",
                        ),
                        Task(
                            id=2,
                            title="Existing",
                            points=3,
                            due_date=None,
                            status=TaskStatus.PROGRESS,
                            body="<p>Existing body</p>",
                        ),
                    ),
                ),
            )
            self.assertIn("number = 2", config_path.read_text(encoding="utf-8"))

    def test_failed_document_update_does_not_increment_number(self) -> None:
        """ドキュメント更新が失敗した場合はタスク番号を変更しない。"""

        with TemporaryDirectory() as directory:
            config_path = _write_config(Path(directory), number=1)
            document_manager = FakeDocumentManager(should_fail=True)

            with self.assertRaisesRegex(RuntimeError, "Document update failed"):
                create_task(
                    "CI setup",
                    config_path=config_path,
                    document_manager=document_manager,
                )

            self.assertIn("number = 1", config_path.read_text(encoding="utf-8"))


def _write_config(directory: Path, *, number: int) -> Path:
    """テスト用の一時 ss4d 設定ファイルを書き込む。"""

    config_path = directory / ".ss4d.toml"
    config_path.write_text(
        'url = "https://example.atlassian.net/wiki"\n'
        'token = "token"\n'
        'page = "123"\n'
        'email = "user@example.com"\n'
        f"number = {number}\n",
        encoding="utf-8",
    )
    return config_path
