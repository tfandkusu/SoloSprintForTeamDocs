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
