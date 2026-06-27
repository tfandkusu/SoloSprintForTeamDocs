"""スプリントのドメインモデル。"""

from dataclasses import dataclass
from datetime import date

from ss4d.model.task import Task


@dataclass(frozen=True)
class Sprint:
    """ドキュメント形式から独立して表現されたスプリント。"""

    start_day: date
    done_point: int
    all_point: int
    tasks: list[Task]
