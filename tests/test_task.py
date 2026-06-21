"""Tests for the task domain model."""

from dataclasses import FrozenInstanceError
from datetime import date
from unittest import TestCase

from ss4d.model import Task, TaskStatus


class TaskStatusTest(TestCase):
    """Tests for task workflow statuses."""

    def test_statuses_have_document_values(self) -> None:
        """Expose the lowercase status values used by task documents."""

        self.assertEqual(
            [status.value for status in TaskStatus],
            ["todo", "progress", "review", "done"],
        )


class TaskTest(TestCase):
    """Tests for the task domain model."""

    def test_task_contains_document_independent_fields(self) -> None:
        """Store every task field without interpreting the HTML body."""

        task = Task(
            id=7,
            title="Create data model",
            points=3,
            due_date=date(2026, 6, 30),
            status=TaskStatus.PROGRESS,
            body="<p>Keep <strong>Confluence</strong> HTML intact.</p>",
        )

        self.assertEqual(task.id, 7)
        self.assertEqual(task.title, "Create data model")
        self.assertEqual(task.points, 3)
        self.assertEqual(task.due_date, date(2026, 6, 30))
        self.assertEqual(task.status, TaskStatus.PROGRESS)
        self.assertEqual(
            task.body,
            "<p>Keep <strong>Confluence</strong> HTML intact.</p>",
        )

    def test_due_date_can_be_missing(self) -> None:
        """Allow tasks that do not have a due date."""

        task = Task(
            id=8,
            title="Unscheduled task",
            points=1,
            due_date=None,
            status=TaskStatus.TODO,
            body="",
        )

        self.assertIsNone(task.due_date)

    def test_task_is_immutable(self) -> None:
        """Prevent accidental mutation while transforming task collections."""

        task = Task(
            id=9,
            title="Review task",
            points=2,
            due_date=None,
            status=TaskStatus.REVIEW,
            body="<p>Review notes</p>",
        )

        with self.assertRaises(FrozenInstanceError):
            task.title = "Changed"  # type: ignore[misc]
