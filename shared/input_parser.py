"""Utilities for parsing free-form user input containing PR URLs."""

from __future__ import annotations

import re
from typing import Tuple


PR_URL_REGEX = re.compile(r"https://github.com/[^/\s]+/[^/\s]+/pull/\d+")


def extract_pr_url_and_request(raw_input: str, default_request: str) -> Tuple[str, str]:
    """Extract the first GitHub PR URL and the remaining request text.

    Args:
        raw_input: Free-form text provided by the user.
        default_request: Fallback instruction when no extra text is supplied.

    Returns:
        Tuple of (pr_url, request_text).

    Raises:
        ValueError: If no GitHub PR URL is found in the input.
    """

    match = PR_URL_REGEX.search(raw_input)
    if not match:
        raise ValueError("No GitHub pull request URL found in input. Please provide a valid GitHub PR URL.")

    pr_url = match.group(0)
    request = raw_input.replace(pr_url, "", 1).strip()

    return pr_url, (request or default_request)


__all__ = ["extract_pr_url_and_request"]