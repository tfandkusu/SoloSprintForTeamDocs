#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ss4d create
# @raycast.mode compact

# Optional parameters:
# @raycast.packageName SoloSprintForTeamDocs
# @raycast.argument1 { "type": "text", "placeholder": "TITLE" }
# @raycast.description Create a task heading in Confluence.

set -e

script_dir="${0:A:h}"
repo_root="${script_dir:h}"

source "${script_dir}/uv.zsh"

cd "${repo_root}"
"${SS4D_UV_BIN}" run ss4d create "$1"
