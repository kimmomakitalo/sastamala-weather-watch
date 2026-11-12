"""Open-Meteo forecast retrieval and response validation."""

import logging
import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests

from .config import (
    FORECAST_HOURS,
    HTTP_TIMEOUT_SECONDS,
    LATITUDE,
    LOCATION_NAME,
    LONGITUDE,
    TIMEZONE,
)
from .models import Forecast, HourlyWeather

LOGGER = logging.getLogger(__name__)
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = ("temperature_2m", "rain", "showers", "snowfall")


class WeatherApiError(RuntimeError):
    """Raised when the forecast service fails or returns invalid data."""


def _number_list(hourly: dict, field: str, expected_length: int) -> list[float]:
    values = hourly.get(field)
    if not isinstance(values, list) or len(values) != expected_length:
        raise WeatherApiError(f"Open-Meteo response has invalid hourly field: {field}")

    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise WeatherApiError(f"Open-Meteo response has non-numeric {field} value")
        number = float(value)
        if not math.isfinite(number):
            raise WeatherApiError(f"Open-Meteo response has non-finite {field} value")
        result.append(number)
    return result


def parse_forecast(payload: object) -> Forecast:
    """Validate an Open-Meteo JSON response and convert timestamps to Helsinki time."""
    if not isinstance(payload, dict):
        raise WeatherApiError("Open-Meteo response is not a JSON object")
    if payload.get("error"):
        raise WeatherApiError(f"Open-Meteo error: {payload.get('reason', 'unknown error')}")

    hourly = payload.get("hourly")
    if not isinstance(hourly, dict):
        raise WeatherApiError("Open-Meteo response is missing hourly forecast data")
    times = hourly.get("time")
    if not isinstance(times, list) or len(times) != FORECAST_HOURS:
        raise WeatherApiError(
            f"Expected {FORECAST_HOURS} hourly forecast times from Open-Meteo"
        )

    temperatures = _number_list(hourly, "temperature_2m", len(times))
    rain = _number_list(hourly, "rain", len(times))
    showers = _number_list(hourly, "showers", len(times))
    snowfall = _number_list(hourly, "snowfall", len(times))

    local_timezone = ZoneInfo(TIMEZONE)
    points = []
    previous_timestamp = None
    for index, timestamp in enumerate(times):
        if isinstance(timestamp, bool) or not isinstance(timestamp, int):
            raise WeatherApiError("Open-Meteo response has an invalid hourly timestamp")
        if previous_timestamp is not None and timestamp - previous_timestamp != 3600:
            raise WeatherApiError("Open-Meteo hourly timestamps are not one hour apart")
        previous_timestamp = timestamp
        local_time = datetime.fromtimestamp(timestamp, timezone.utc).astimezone(
            local_timezone
        )
        points.append(
            HourlyWeather(
                time=local_time,
                temperature_c=temperatures[index],
                rain_mm=rain[index],
                showers_mm=showers[index],
                snowfall_cm=snowfall[index],
            )
        )

    return Forecast(points=tuple(points))


def fetch_forecast() -> Forecast:
    """Fetch the next 24 hours of hourly weather for Sastamala."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ",".join(HOURLY_FIELDS),
        "forecast_hours": FORECAST_HOURS,
        "timezone": TIMEZONE,
        "timeformat": "unixtime",
    }
    LOGGER.info(
        "Haetaan %s:n seuraavan %s tunnin ennuste Open-Meteosta",
        LOCATION_NAME,
        FORECAST_HOURS,
    )
    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise WeatherApiError(f"Could not retrieve a valid Open-Meteo forecast: {error}") from error

    forecast = parse_forecast(payload)
    LOGGER.info(
        "Ennusteessa on %s tuntia, alkaen %s",
        len(forecast.points),
        forecast.points[0].time,
    )
    return forecast
