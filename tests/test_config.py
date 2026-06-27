from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from ss4d.config import ConfigError, increment_number, load_config


class ConfigTest(TestCase):
    def test_missing_config_file_is_rejected(self) -> None:
        """ファイルが存在しない場合は設定の読み込みを拒否する。"""

        with self.assertRaisesRegex(ConfigError, "Config file not found"):
            load_config(Path("/missing/.ss4d.toml"))

    def test_missing_required_field_is_rejected(self) -> None:
        """必須フィールドが欠けている設定を拒否する。"""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                "number = 1\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError,
                "Config field 'page' must be a non-empty string.",
            ):
                load_config(config_path)

    def test_non_integer_number_is_rejected(self) -> None:
        """タスク番号が整数でない設定を拒否する。"""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                'page = "123"\n'
                'number = "1"\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError,
                "Config field 'number' must be an integer.",
            ):
                load_config(config_path)

    def test_email_is_loaded(self) -> None:
        """Atlassian アカウントのメールアドレスを読み込む。"""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                'page = "123"\n'
                "number = 1\n"
                'email = "user@example.com"\n',
                encoding="utf-8",
            )

            self.assertEqual(load_config(config_path).email, "user@example.com")

    def test_missing_email_is_rejected(self) -> None:
        """Atlassian アカウントのメールアドレスが欠けている設定を拒否する。"""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                'page = "123"\n'
                "number = 1\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError,
                "Config field 'email' must be a non-empty string.",
            ):
                load_config(config_path)

    def test_empty_email_is_rejected(self) -> None:
        """メールアドレスが空白の場合は拒否する。"""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                'page = "123"\n'
                "number = 1\n"
                'email = ""\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ConfigError,
                "Config field 'email' must be a non-empty string.",
            ):
                load_config(config_path)

    def test_increment_number_updates_config_file(self) -> None:
        """設定ファイルに保存されたタスク番号をインクリメントする。"""

        with TemporaryDirectory() as directory:
            config_path = Path(directory) / ".ss4d.toml"
            config_path.write_text(
                'url = "https://example.atlassian.net/wiki"\n'
                'token = "token"\n'
                'page = "123"\n'
                'email = "user@example.com"\n'
                "number = 1\n",
                encoding="utf-8",
            )

            increment_number(config_path)

            self.assertEqual(load_config(config_path).number, 2)
