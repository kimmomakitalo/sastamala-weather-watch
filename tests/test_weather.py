from datetime import datetime, timezone

import pytest

from weather_watch.config import FORECAST_HOURS
from weather_watch.weather import WeatherApiError, parse_forecast


def valid_payload() -> dict:
    start = int(datetime(2026, 1, 10, 14, tzinfo=timezone.utc).timestamp())
    return {
        "hourly": {
            "time": [start + hour * 3600 for hour in range(FORECAST_HOURS)],
            "temperature_2m": [1.0] * FORECAST_HOURS,
            "rain": [0.0] * FORECAST_HOURS,
            "showers": [0.0] * FORECAST_HOURS,
            "snowfall": [0.0] * FORECAST_HOURS,
        }
    }


def test_parse_forecast_converts_unix_times_to_helsinki_time() -> None:
    forecast = parse_forecast(valid_payload())

    assert len(forecast.points) == FORECAST_HOURS
    assert forecast.points[0].time.isoformat() == "2026-01-10T16:00:00+02:00"


def test_parse_forecast_rejects_missing_hourly_variable() -> None:
    payload = valid_payload()
    del payload["hourly"]["snowfall"]

    with pytest.raises(WeatherApiError, match="snowfall"):
        parse_forecast(payload)


def test_parse_forecast_rejects_wrong_number_of_hours() -> None:
    payload = valid_payload()
    payload["hourly"]["time"].pop()

    with pytest.raises(WeatherApiError, match="Expected 24"):
        parse_forecast(payload)


def test_parse_forecast_rejects_irregular_timestamps() -> None:
    payload = valid_payload()
    payload["hourly"]["time"][4] += 60

    with pytest.raises(WeatherApiError, match="one hour apart"):
        parse_forecast(payload)
