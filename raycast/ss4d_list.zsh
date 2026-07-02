#!/bin/zsh

# 必須パラメーター:
# @raycast.schemaVersion 1
# @raycast.title ss4d list
# @raycast.mode fullOutput

# 任意パラメーター:
# @raycast.packageName SoloSprintForTeamDocs
# @raycast.argument1 { "type": "dropdown", "placeholder": "SCOPE", "data": [{"title": "remaining", "value": "remaining"}, {"title": "all", "value": "all"}] }
# @raycast.description List tasks from Confluence.

set -e

# このスクリプトのディレクトリの絶対パスを取得する。
script_dir="${0:A:h}"

# リポジトリルートは raycast ディレクトリの親ディレクトリ。
repo_root="${script_dir:h}"

# このスクリプトと同じディレクトリから uv 解決用スクリプトを読み込む。
source "${script_dir}/uv.zsh"

# uv が pyproject.toml を見つけられるようにリポジトリルートから ss4d を実行する。
cd "${repo_root}"

if [[ -n "$1" ]]; then
  "${SS4D_UV_BIN}" run ss4d list "$1"
else
  "${SS4D_UV_BIN}" run ss4d list
fi
