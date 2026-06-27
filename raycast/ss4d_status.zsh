#!/bin/zsh

# 必須パラメーター:
# @raycast.schemaVersion 1
# @raycast.title ss4d status
# @raycast.mode compact

# 任意パラメーター:
# @raycast.packageName SoloSprintForTeamDocs
# @raycast.argument1 { "type": "text", "placeholder": "NUMBER" }
# @raycast.argument2 { "type": "dropdown", "placeholder": "STATUS", "data": [{"title": "todo", "value": "todo"}, {"title": "progress", "value": "progress"}, {"title": "review", "value": "review"}, {"title": "done", "value": "done"}] }
# @raycast.description Update a task status in Confluence.

set -e

# このスクリプトのディレクトリの絶対パスを取得する。
script_dir="${0:A:h}"

# リポジトリルートは raycast ディレクトリの親ディレクトリ。
repo_root="${script_dir:h}"

# このスクリプトと同じディレクトリから uv 解決用スクリプトを読み込む。
source "${script_dir}/uv.zsh"

# uv が pyproject.toml を見つけられるようにリポジトリルートから ss4d を実行する。
cd "${repo_root}"

"${SS4D_UV_BIN}" run ss4d status "$1" "$2"
