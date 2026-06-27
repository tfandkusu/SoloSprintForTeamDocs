---
name: create-pr
description: Use this skill when creating a pull request. Also use it when the user provides a number starting with `#` and asks to create or implement something.
---

# Pull Request Workflow

- If a number starting with `#` is provided, treat it as a GitHub issue number, read the issue, and implement it.
- Do not rewrite `README.md`.

# Branch Name

- If an issue is specified, use `issue_NUMBER` as the pull request branch name.
- Otherwise, choose a concise branch name that describes the work.

# Branch Creation

- Switch to the `main` branch, pull the latest changes from the remote, then create the pull request branch.

# Pull Request Title

- If an issue is specified, use the same title as the issue.
- If no issue is specified, use a title that describes the change.

# Pull Request Body

- Follow `.github/PULL_REQUEST_TEMPLATE.md`.
- Describe the final changes relative to the target branch.

# Definition of Done

- The work is complete only after all requested changes are committed, pushed, and the pull request body is updated.
