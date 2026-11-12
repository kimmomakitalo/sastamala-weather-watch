"""Command-line entry point for the weather watch."""

import argparse
import logging

from .analysis import analyze_forecast
from .github_issues import GitHubIssueClient, publish_alerts
from .scheduling import is_scheduled_local_hour
from .weather import fetch_forecast

LOGGER = logging.getLogger("weather_watch")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Sastamala's next 24-hour forecast.")
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Skip the run unless it is currently the scheduled Finnish local hour.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if args.scheduled:
        if not is_scheduled_local_hour():
            LOGGER.info(
                "Ohitetaan väärän UTC-ajon kutsu: Suomen paikallisaika ei ole "
                "tavoitetunnin kohdalla."
            )
            return 0

    forecast = fetch_forecast()
    alerts = analyze_forecast(forecast)
    if not alerts:
        LOGGER.info("Varoituksia ei syntynyt; GitHub Issuea ei luoda.")
        return 0

    client = GitHubIssueClient.from_environment()
    publish_alerts(alerts, client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
