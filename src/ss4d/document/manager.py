"""ドキュメントマネージャーの抽象化。"""

from typing import Protocol, runtime_checkable

from ss4d.model.sprint import Sprint


@runtime_checkable
class DocumentManager(Protocol):
    """タスク処理で使う抽象ドキュメントマネージャー。"""

    def read_sprint(self) -> Sprint:
        """設定されたドキュメントからスプリント情報を読み込む。"""
        ...

    def write_sprint(self, sprint: Sprint) -> None:
        """指定されたスプリント情報で設定済みのドキュメントを上書きする。"""
        ...
