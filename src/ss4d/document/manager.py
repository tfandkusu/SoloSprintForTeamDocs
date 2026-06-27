"""ドキュメントマネージャーの抽象化。"""

from typing import Protocol, runtime_checkable

from ss4d.model.task import Task


@runtime_checkable
class DocumentManager(Protocol):
    """タスク処理で使う抽象ドキュメントマネージャー。"""

    def read_tasks(self) -> list[Task]:
        """設定されたドキュメントからすべてのタスクを読み込む。"""
        ...

    def write_tasks(self, tasks: list[Task]) -> None:
        """指定されたタスクで設定済みのドキュメントを上書きする。"""
        ...
