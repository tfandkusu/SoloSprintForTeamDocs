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

- Write the pull request title in English.
- If an issue is specified and its title is not English, translate or summarize the issue title into a concise English pull request title.
- If an issue is specified and its title is already English, use the same title as the issue.
- If no issue is specified, use an English title that describes the change.

# Pull Request Body

- Follow `.github/PULL_REQUEST_TEMPLATE.md`.
- Describe the final changes relative to the target branch.
- Write the pull request body in English.

# Definition of Done

- The work is complete only after all requested changes are committed, pushed, and the pull request body is updated.
