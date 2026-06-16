#!/bin/zsh

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title ss4d status
# @raycast.mode compact

# Optional parameters:
# @raycast.packageName SoloSprintForTeamDocs
# @raycast.argument1 { "type": "text", "placeholder": "NUMBER" }
# @raycast.argument2 { "type": "dropdown", "placeholder": "STATUS", "data": [{"title": "TODO", "value": "TODO"}, {"title": "PROGRESS", "value": "PROGRESS"}, {"title": "REVIEW", "value": "REVIEW"}, {"title": "DONE", "value": "DONE"}] }
# @raycast.description Update a task status in Confluence.

set -e

# Get the absolute path to this script's directory.
script_dir="${0:A:h}"

# The repository root is the parent directory of the raycast directory.
repo_root="${script_dir:h}"

# Load the uv resolver from the same directory as this script.
source "${script_dir}/uv.zsh"

# Run ss4d from the repository root so uv can find pyproject.toml.
cd "${repo_root}"

"${SS4D_UV_BIN}" run ss4d status "$1" "$2"
