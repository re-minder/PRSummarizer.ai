"""Shared helpers for fetching GitHub PR information.

This module centralises the PyGithub interaction so multiple agents can
reuse the same logic (and future caching) without duplicating code.
"""

from __future__ import annotations

import os
import re
from typing import Callable, Optional

from github import Github
from dotenv import load_dotenv

# Load env vars once so modules using this helper don't need to repeat it.
load_dotenv()

TrackActionFn = Callable[[str, str, str], None]


def fetch_pr_info(
    pr_url: str,
    track_action: Optional[TrackActionFn] = None,
) -> str:
    """Fetch a GitHub PR snapshot for agent consumption.

    Args:
        pr_url: GitHub pull request URL (``https://github.com/org/repo/pull/123``).
        track_action: Optional callback used by callers to surface progress
            updates to UI/telemetry layers (signature: ``action, detail, status``).

    Returns:
        A human-readable string summarising key PR metadata. Errors are
        returned as string messages so agent tool invocations can surface them
        directly.
    """

    if track_action:
        track_action("fetch_pr_info", f"Fetching data from {pr_url}", "running")

    match = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        if track_action:
            track_action("fetch_pr_info", "Invalid PR URL format", "failed")
        return f"Invalid PR URL format: {pr_url}"

    owner, repo, pr_num = match.groups()

    token = (
        os.getenv("GITHUB_TOKEN")
        or os.getenv("GITHUB_ACCESS_TOKEN")
        or os.getenv("GITHUB_PAT")
    )
    github_client = Github(token) if token else Github()

    try:
        repository = github_client.get_repo(f"{owner}/{repo}")
        pr = repository.get_pull(int(pr_num))

        files = [f.filename for f in pr.get_files()]
        comments = [
            f"{c.user.login}: {c.body[:100]}" for c in list(pr.get_issue_comments())[:5]
        ]

        summary = (
            f"PR #{pr_num} in {owner}/{repo}\n"
            f"Title: {pr.title}\n"
            f"Author: {pr.user.login}\n"
            f"State: {pr.state} {'(Draft)' if pr.draft else ''}\n"
            f"Description: {pr.body[:500] if pr.body else 'No description'}\n"
            f"Files changed: {pr.changed_files} files ({pr.additions} additions, {pr.deletions} deletions)\n"
            f"Files: {', '.join(files[:10])}\n"
            f"Merge status: {'Merged' if pr.merged else 'Not merged'}\n"
            f"Comments: {'; '.join(comments) if comments else 'No comments'}"
        )

        if track_action:
            detail = f"Retrieved PR #{pr_num}: {pr.changed_files} files changed"
            track_action("fetch_pr_info", detail, "completed")

        return summary

    except Exception as exc:  # pragma: no cover - network / API errors
        if track_action:
            track_action("fetch_pr_info", f"Error: {exc}", "failed")
        return f"Error fetching PR: {exc}"


__all__ = ["fetch_pr_info"]