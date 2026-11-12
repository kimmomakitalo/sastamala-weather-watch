from unittest.mock import Mock

from weather_watch.github_issues import GitHubIssueClient, publish_alerts
from weather_watch.models import WeatherAlert


def test_creates_then_closes_issue(monkeypatch) -> None:
    post = Mock()
    post.return_value.json.return_value = {
        "number": 42,
        "html_url": "https://github.com/example/weather/issues/42",
    }
    patch = Mock()
    monkeypatch.setattr("weather_watch.github_issues.requests.post", post)
    monkeypatch.setattr("weather_watch.github_issues.requests.patch", patch)
    client = GitHubIssueClient("token", "example/weather")
    alert = WeatherAlert("pakkanen", "Pakkanen – 2026-01-10", "Kylmää.")

    issue_url = client.create_and_close(alert)

    assert issue_url == "https://github.com/example/weather/issues/42"
    assert post.call_args.kwargs["json"]["title"] == alert.title
    assert patch.call_args.args[0].endswith("/issues/42")
    assert patch.call_args.kwargs["json"] == {"state": "closed"}


def test_publish_alerts_skips_duplicate_titles() -> None:
    client = Mock()
    alert = WeatherAlert("pakkanen", "Pakkanen – 2026-01-10", "Kylmää.")

    publish_alerts([alert, alert], client)

    client.create_and_close.assert_called_once_with(alert)


def test_client_requires_token_and_repository() -> None:
    import pytest

    from weather_watch.github_issues import GitHubIssueError

    with pytest.raises(GitHubIssueError, match="GITHUB_TOKEN"):
        GitHubIssueClient("", "example/weather")
    with pytest.raises(GitHubIssueError, match="GITHUB_REPOSITORY"):
        GitHubIssueClient("token", "")
