"""Create and immediately close GitHub Issues for weather alerts."""

import logging
import os

import requests

from .config import HTTP_TIMEOUT_SECONDS
from .models import WeatherAlert

LOGGER = logging.getLogger(__name__)
GITHUB_API_URL = "https://api.github.com"


class GitHubIssueError(RuntimeError):
    """Raised when a weather Issue cannot be created or closed."""


class GitHubIssueClient:
    def __init__(self, token: str, repository: str) -> None:
        if not token:
            raise GitHubIssueError("GITHUB_TOKEN is required to publish an alert")
        if not repository or "/" not in repository:
            raise GitHubIssueError("GITHUB_REPOSITORY must be set as owner/repository")
        self._token = token
        self._repository = repository

    @classmethod
    def from_environment(cls) -> "GitHubIssueClient":
        return cls(
            token=os.environ.get("GITHUB_TOKEN", ""),
            repository=os.environ.get("GITHUB_REPOSITORY", ""),
        )

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_and_close(self, alert: WeatherAlert) -> str:
        url = f"{GITHUB_API_URL}/repos/{self._repository}/issues"
        try:
            response = requests.post(
                url,
                headers=self._headers,
                json={"title": alert.title, "body": alert.body},
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            issue = response.json()
        except (requests.RequestException, ValueError) as error:
            raise GitHubIssueError(f"Could not create GitHub Issue: {error}") from error

        number = issue.get("number") if isinstance(issue, dict) else None
        issue_url = issue.get("html_url") if isinstance(issue, dict) else None
        if not isinstance(number, int) or not isinstance(issue_url, str):
            raise GitHubIssueError("GitHub returned an invalid Issue response")

        try:
            close_response = requests.patch(
                f"{url}/{number}",
                headers=self._headers,
                json={"state": "closed"},
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            close_response.raise_for_status()
        except requests.RequestException as error:
            raise GitHubIssueError(
                f"Issue #{number} was created but could not be closed: {error}"
            ) from error

        LOGGER.info("Luotiin ja suljettiin Issue #%s: %s", number, issue_url)
        return issue_url


def publish_alerts(alerts: list[WeatherAlert], client: GitHubIssueClient) -> None:
    """Publish each distinct alert title at most once in this invocation."""
    published_titles = set()
    for alert in alerts:
        if alert.title in published_titles:
            LOGGER.warning("Ohitetaan saman ajon päällekkäinen varoitus: %s", alert.title)
            continue
        published_titles.add(alert.title)
        client.create_and_close(alert)
