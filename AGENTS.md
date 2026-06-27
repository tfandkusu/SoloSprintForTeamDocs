# リポジトリガイドライン

- すべてのメソッドに docstring を追加する。

## PR 作成ガイドライン

PR 作成前に以下のコマンドでフォーマットを整える。

```sh
uv run ruff format .
```

次にこちらのコマンドで問題がないことを確認する。

```sh
uv run ruff check .
uv run pyright
uv run pytest
```
