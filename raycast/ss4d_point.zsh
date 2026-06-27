#!/bin/zsh

# 必須パラメーター:
# @raycast.schemaVersion 1
# @raycast.title ss4d point
# @raycast.mode compact

# 任意パラメーター:
# @raycast.packageName SoloSprintForTeamDocs
# @raycast.argument1 { "type": "text", "placeholder": "NUMBER" }
# @raycast.argument2 { "type": "dropdown", "placeholder": "POINT", "data": [{"title": "1", "value": "1"}, {"title": "2", "value": "2"}, {"title": "3", "value": "3"}, {"title": "5", "value": "5"}, {"title": "8", "value": "8"}, {"title": "13", "value": "13"}, {"title": "21", "value": "21"}] }
# @raycast.description Update a task point in Confluence.

set -e

# このスクリプトのディレクトリの絶対パスを取得する。
script_dir="${0:A:h}"

# リポジトリルートは raycast ディレクトリの親ディレクトリ。
repo_root="${script_dir:h}"

# このスクリプトと同じディレクトリから uv 解決用スクリプトを読み込む。
source "${script_dir}/uv.zsh"

# uv が pyproject.toml を見つけられるようにリポジトリルートから ss4d を実行する。
cd "${repo_root}"

"${SS4D_UV_BIN}" run ss4d point "$1" "$2"
