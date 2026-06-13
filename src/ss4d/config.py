"""Configuration helpers for ss4d."""

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import tomlkit
from tomlkit.toml_document import TOMLDocument

CONFIG_PATH = Path.home() / ".ss4d.toml"


class ConfigError(Exception):
    """Raised when the ss4d config file cannot be used."""


@dataclass(frozen=True)
class Config:
    """Runtime configuration loaded from .ss4d.toml."""

    url: str
    token: str
    page: str
    number: int
    email: str


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Load and validate ss4d configuration."""

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
    """Increment the configured task number in place."""

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    raw_config = _get_root_table(document)
    number = _require_int(raw_config, "number")
    raw_config["number"] = number + 1
    path.write_text(tomlkit.dumps(document), encoding="utf-8")


def _get_root_table(document: TOMLDocument) -> dict[str, object]:
    """Return the root TOML document as a mutable mapping."""

    return cast(dict[str, object], document)


def _require_string(raw_config: dict[str, object], field_name: str) -> str:
    """Return a required non-empty string config field."""

    value = raw_config.get(field_name)
    if not isinstance(value, str) or value == "":
        raise ConfigError(f"Config field '{field_name}' must be a non-empty string.")
    return value


def _require_int(raw_config: dict[str, object], field_name: str) -> int:
    """Return a required integer config field."""

    value = raw_config.get(field_name)
    if not isinstance(value, int):
        raise ConfigError(f"Config field '{field_name}' must be an integer.")
    return value
