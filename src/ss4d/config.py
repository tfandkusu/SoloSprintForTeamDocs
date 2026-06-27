"""ss4d の設定ヘルパー。"""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import tomlkit
from tomlkit.toml_document import TOMLDocument

CONFIG_PATH = Path.home() / ".ss4d.toml"


class ConfigError(Exception):
    """ss4d 設定ファイルを利用できない場合に送出される例外。"""


@dataclass(frozen=True)
class Config:
    """.ss4d.toml から読み込まれる実行時設定。"""

    url: str
    token: str
    page: str
    number: int
    email: str


def load_config(path: Path = CONFIG_PATH) -> Config:
    """ss4d 設定を読み込み検証する。"""

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    raw_config = _get_root_table(document)

    url = _require_string(raw_config, "url")
    token = _require_string(raw_config, "token")
    page = _require_string(raw_config, "page")
    number = _require_int(raw_config, "number")
    email = _require_string(raw_config, "email")

    return Config(url=url, token=token, page=page, number=number, email=email)


def increment_number(path: Path = CONFIG_PATH) -> None:
    """設定済みのタスク番号をその場でインクリメントする。"""

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    raw_config = _get_root_table(document)
    number = _require_int(raw_config, "number")
    raw_config["number"] = number + 1
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def _get_root_table(document: TOMLDocument) -> dict[str, object]:
    """ルート TOML ドキュメントをミュータブルなマッピングとして返す。"""

    return cast(dict[str, object], document)


def _require_string(raw_config: dict[str, object], field_name: str) -> str:
    """必須の空でない文字列設定フィールドを返す。"""

    value = raw_config.get(field_name)
    if not isinstance(value, str) or value == "":
        raise ConfigError(f"Config field '{field_name}' must be a non-empty string.")
    return value


def _require_int(raw_config: dict[str, object], field_name: str) -> int:
    """必須の整数設定フィールドを返す。"""

    value = raw_config.get(field_name)
    if not isinstance(value, int):
        raise ConfigError(f"Config field '{field_name}' must be an integer.")
    return value
