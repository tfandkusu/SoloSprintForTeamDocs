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

# Get the absolute path to this script's directory.
script_dir="${0:A:h}"

# The repository root is the parent directory of the raycast directory.
repo_root="${script_dir:h}"

# Load the uv resolver from the same directory as this script.
source "${script_dir}/uv.zsh"

# Run ss4d from the repository root so uv can find pyproject.toml.
cd "${repo_root}"

# Use the title passed from Raycast as the ss4d create argument.
"${SS4D_UV_BIN}" run ss4d create "$1"
