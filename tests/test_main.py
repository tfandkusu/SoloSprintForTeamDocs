from unittest import TestCase
from unittest.mock import patch

from typer.testing import CliRunner

from ss4d.main import app


class MainTest(TestCase):
    def test_create_outputs_created_task_number(self) -> None:
        """Output only the created task number on success."""

        runner = CliRunner()

        with patch("ss4d.main.create_task", return_value=7):
            result = runner.invoke(app, ["create", "CI setup"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Created task #7\n")

    def test_sort_outputs_sorted_tasks(self) -> None:
        """Output a sort completion message on success."""

        runner = CliRunner()

        with patch("ss4d.main.sort_tasks") as sort_tasks:
            result = runner.invoke(app, ["sort"])

        sort_tasks.assert_called_once_with()
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Sorted tasks\n")

    def test_status_outputs_updated_task_status(self) -> None:
        """Output a status update completion message on success."""

        runner = CliRunner()

        with patch("ss4d.main.update_task_status", return_value="DONE") as update_task_status:
            result = runner.invoke(app, ["status", "7", "done"])

        update_task_status.assert_called_once_with(7, "done")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output, "Updated task #7 to DONE\n")

    def test_status_outputs_error_when_update_fails(self) -> None:
        """Output a status update error when the process fails."""

        runner = CliRunner()

        with patch(
            "ss4d.main.update_task_status",
            side_effect=ValueError("Status must be one of: TODO, PROGRESS, REVIEW, DONE."),
        ):
            result = runner.invoke(app, ["status", "7", "blocked"])

        self.assertEqual(result.exit_code, 1)
        self.assertEqual(
            result.stderr,
            "Failed to update task status: "
            "Status must be one of: TODO, PROGRESS, REVIEW, DONE.\n",
        )
