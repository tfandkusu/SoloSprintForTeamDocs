from unittest import TestCase
from unittest.mock import patch

from typer.testing import CliRunner

from ss4d.main import app


class MainTest(TestCase):
    def test_create_outputs_created_task_number(self) -> None:
        """成功時に作成されたタスク番号だけを出力する。"""

        runner = CliRunner()

        with patch("ss4d.main.create_task", return_value=7):
            result = runner.invoke(app, ["create", "CI setup"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Created task #7\n")

    def test_sort_outputs_sorted_tasks(self) -> None:
        """成功時に並び替え完了メッセージを出力する。"""

        runner = CliRunner()

        with patch("ss4d.main.sort_tasks") as sort_tasks:
            result = runner.invoke(app, ["sort"])

        sort_tasks.assert_called_once_with()
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Sorted tasks\n")

    def test_status_outputs_updated_task_status(self) -> None:
        """成功時にステータス更新完了メッセージを出力する。"""

        runner = CliRunner()

        with patch(
            "ss4d.main.update_task_status", return_value="DONE"
        ) as update_task_status:
            result = runner.invoke(app, ["status", "7", "done"])

        update_task_status.assert_called_once_with(7, "done")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Updated task #7 to DONE\n")

    def test_status_outputs_error_when_update_fails(self) -> None:
        """処理失敗時にステータス更新エラーを出力する。"""

        runner = CliRunner()

        with patch(
            "ss4d.main.update_task_status",
            side_effect=ValueError(
                "Status must be one of: TODO, PROGRESS, REVIEW, DONE."
            ),
        ):
            result = runner.invoke(app, ["status", "7", "blocked"])

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            result.stderr,
            "Failed to update task status: "
            "Status must be one of: TODO, PROGRESS, REVIEW, DONE.\n",
        )

    def test_due_outputs_updated_task_due_date(self) -> None:
        """成功時に期限日更新完了メッセージを出力する。"""

        runner = CliRunner()

        with patch(
            "ss4d.main.update_task_due_date", return_value="2026-06-30"
        ) as update_task_due_date:
            result = runner.invoke(app, ["due", "7", "next Tuesday"])

        update_task_due_date.assert_called_once_with(7, "next Tuesday")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Updated task #7 due date to 2026-06-30\n")

    def test_due_outputs_error_when_update_fails(self) -> None:
        """処理失敗時に期限日更新エラーを出力する。"""

        runner = CliRunner()

        with patch(
            "ss4d.main.update_task_due_date",
            side_effect=ValueError("Could not parse deadline: someday"),
        ):
            result = runner.invoke(app, ["due", "7", "someday"])

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            result.stderr,
            "Failed to update task due date: Could not parse deadline: someday\n",
        )

    def test_point_outputs_updated_task_point(self) -> None:
        """成功時にポイント更新完了メッセージを出力する。"""

        runner = CliRunner()

        with patch("ss4d.main.update_task_point", return_value=8) as update_task_point:
            result = runner.invoke(app, ["point", "7", "8"])

        update_task_point.assert_called_once_with(7, 8)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Updated task #7 point to 8\n")

    def test_point_outputs_error_when_update_fails(self) -> None:
        """処理失敗時にポイント更新エラーを出力する。"""

        runner = CliRunner()

        with patch(
            "ss4d.main.update_task_point",
            side_effect=ValueError("Point must be 1 or greater."),
        ):
            result = runner.invoke(app, ["point", "7", "0"])

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            result.stderr,
            "Failed to update task point: Point must be 1 or greater.\n",
        )

    def test_list_outputs_remaining_tasks_by_default(self) -> None:
        """成功時に未完了タスク一覧を出力する。"""

        runner = CliRunner()

        with (
            patch("ss4d.main.list_tasks", return_value=("task",)) as mocked_list_tasks,
            patch("ss4d.main.format_task_lines", return_value=["line 1", "line 2"])
            as mocked_format_task_lines,
        ):
            result = runner.invoke(app, ["list"], color=True)

        mocked_list_tasks.assert_called_once_with(show_all=False)
        mocked_format_task_lines.assert_called_once_with(("task",))
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "line 1\nline 2\n")

    def test_list_outputs_all_tasks_when_requested(self) -> None:
        """all 指定時に全件表示モードで一覧を取得する。"""

        runner = CliRunner()

        with patch("ss4d.main.list_tasks", return_value=()) as mocked_list_tasks:
            result = runner.invoke(app, ["list", "all"])

        mocked_list_tasks.assert_called_once_with(show_all=True)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "No tasks found\n")

    def test_list_outputs_error_for_unknown_scope(self) -> None:
        """不正な一覧スコープを指定したときはエラーを出力する。"""

        runner = CliRunner()

        result = runner.invoke(app, ["list", "everything"])

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            result.stderr,
            "Failed to list tasks: List scope must be either 'remaining' or 'all'.\n",
        )
