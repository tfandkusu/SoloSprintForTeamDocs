"""Confluence HTML 本文のパーサーとシリアライザー。"""

import re
from collections.abc import Mapping
from datetime import date, datetime
from typing import cast

import tomlkit
from bs4 import BeautifulSoup
from bs4.element import PageElement, Tag

from ss4d.model.sprint import Sprint
from ss4d.model.task import Task
from ss4d.model.task_status import TaskStatus
from ss4d.process.common.calculate_point import (
    calculate_all_point,
    calculate_done_point,
)


def parse_storage_sprint(body: str) -> Sprint:
    """Confluence storage 形式の本文からスプリント情報を解析する。"""

    tasks = parse_storage_tasks(body)
    sprint = _parse_sprint_info(body, tasks)
    if sprint is not None:
        return sprint

    return Sprint(
        start_day=date.today(),
        done_point=calculate_done_point(tasks),
        all_point=calculate_all_point(tasks),
        tasks=tasks,
    )


def parse_storage_tasks(body: str) -> list[Task]:
    """Confluence storage 形式の本文からタスクセクションを解析する。"""

    return [_parse_task(section) for section in _split_h1_sections(body)]


def _parse_task(section_body: str) -> Task:
    """h1 で始まる storage 形式セクション 1 件をタスクに解析する。"""

    soup = BeautifulSoup(section_body, "html.parser")
    h1 = soup.find("h1")
    if not isinstance(h1, Tag):
        raise RuntimeError("Task section did not include an h1 tag.")

    number = _extract_task_number(h1)
    if number is None:
        raise RuntimeError("Task heading did not include a task number.")

    points_match = re.search(r"#\d+\[(\d+)\]", h1.get_text())
    points = int(points_match.group(1)) if points_match is not None else 1
    status_name = _extract_status(h1).lower() or TaskStatus.TODO.value
    try:
        status = TaskStatus(status_name)
    except ValueError:
        status = TaskStatus.TODO

    heading = BeautifulSoup(str(h1), "html.parser").find("h1")
    if not isinstance(heading, Tag):
        raise RuntimeError("Task section did not include an h1 tag.")
    for element in heading.find_all(
        ["time", "ac:structured-macro"],
    ):
        element.decompose()
    title = re.sub(r"^#\d+(?:\[\d+\])?", "", heading.get_text()).strip()

    section_elements = list(soup.contents)
    return Task(
        id=number,
        title=title,
        points=points,
        due_date=_extract_due_date(h1),
        status=status,
        body=_serialize(section_elements[1:]),
    )


def _split_h1_sections(body: str) -> list[str]:
    """HTML 本文を h1 で始まるセクション文字列へ分割する。"""

    soup = BeautifulSoup(body, "html.parser")
    contents = list(soup.contents)
    h1_indexes = [
        index for index, element in enumerate(contents) if _is_tag(element, "h1")
    ]

    return [
        _serialize(contents[start:end])
        for start, end in zip(h1_indexes, [*h1_indexes[1:], len(contents)])
    ]


def _parse_sprint_info(body: str, tasks: list[Task]) -> Sprint | None:
    """先頭 TOML コードブロックからスプリント情報を解析する。"""

    raw_toml = _extract_leading_toml(body)
    if raw_toml is None:
        return None

    parsed = cast(Mapping[str, object], tomlkit.parse(raw_toml))
    raw_start_day = parsed.get("start_day")
    if not isinstance(raw_start_day, str):
        return None

    return Sprint(
        start_day=datetime.strptime(raw_start_day, "%Y/%m/%d").date(),
        done_point=_get_int(parsed.get("done_point"), calculate_done_point(tasks)),
        all_point=_get_int(parsed.get("all_point"), calculate_all_point(tasks)),
        tasks=tasks,
    )


def _extract_leading_toml(body: str) -> str | None:
    """本文先頭の TOML コードブロック本文を抽出する。"""

    soup = BeautifulSoup(body, "html.parser")
    for element in soup.contents:
        if _is_blank_text(element):
            continue
        if not isinstance(element, Tag) or not _is_code_macro(element):
            return None
        language = element.find("ac:parameter", attrs={"ac:name": "language"})
        if isinstance(language, Tag) and language.get_text(strip=True) != "toml":
            return None
        plain_text = element.find("ac:plain-text-body")
        if not isinstance(plain_text, Tag):
            return None
        return plain_text.get_text()

    return None


def _get_int(value: object, default: int) -> int:
    """TOML 値を int として返し、未指定や不正値ならデフォルト値を返す。"""

    return value if isinstance(value, int) else default


def _extract_due_date(h1: Tag) -> date | None:
    """h1 タグから最初の有効な期限日を抽出する。"""

    time = h1.find("time")
    if not isinstance(time, Tag):
        return None

    raw_datetime = time.get("datetime")
    if not isinstance(raw_datetime, str):
        return None

    try:
        return date.fromisoformat(raw_datetime)
    except ValueError:
        return None


def _extract_status(h1: Tag) -> str:
    """h1 タグから最初のステータスマクロタイトルを抽出する。"""

    status_macro = h1.find("ac:structured-macro", attrs={"ac:name": "status"})
    if not isinstance(status_macro, Tag):
        return ""

    title = status_macro.find("ac:parameter", attrs={"ac:name": "title"})
    if not isinstance(title, Tag):
        return ""

    return title.get_text(strip=True)


def _extract_task_number(h1: Tag) -> int | None:
    """h1 タグから最初のタスク番号を抽出する。"""

    match = re.search(r"#(\d+)(?!\d)", h1.get_text())
    if match is None:
        return None
    return int(match.group(1))


def _is_tag(element: PageElement, name: str) -> bool:
    """要素が指定名のタグかどうかを返す。"""

    return isinstance(element, Tag) and element.name == name


def _is_code_macro(element: Tag) -> bool:
    """要素が Confluence の code macro かどうかを返す。"""

    return element.name == "ac:structured-macro" and element.get("ac:name") == "code"


def _is_blank_text(element: PageElement) -> bool:
    """要素が空白だけのテキストノードかどうかを返す。"""

    return not isinstance(element, Tag) and str(element).strip() == ""


def _serialize(elements: list[PageElement]) -> str:
    """解析済み要素を storage 形式のフラグメントへシリアライズする。"""

    return "".join(str(element) for element in elements)
