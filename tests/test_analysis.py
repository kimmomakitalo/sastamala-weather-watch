from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from weather_watch.analysis import analyze_forecast
from weather_watch.config import FROST_THRESHOLD_C, SNOWFALL_THRESHOLD_CM
from weather_watch.models import Forecast, HourlyWeather

HELSINKI = ZoneInfo("Europe/Helsinki")
START = datetime(2026, 1, 10, 16, tzinfo=HELSINKI)


def point(
    hour: int,
    *,
    temperature: float = 5.0,
    rain: float = 0.0,
    showers: float = 0.0,
    snowfall: float = 0.0,
) -> HourlyWeather:
    return HourlyWeather(
        time=START + timedelta(hours=hour),
        temperature_c=temperature,
        rain_mm=rain,
        showers_mm=showers,
        snowfall_cm=snowfall,
    )


def forecast(*points: HourlyWeather) -> Forecast:
    return Forecast(points=tuple(points))


def test_frost_alert_includes_daily_minimum_and_temperature() -> None:
    alerts = analyze_forecast(forecast(point(0, temperature=1), point(1, temperature=-4)))

    frost = next(alert for alert in alerts if alert.kind == "pakkanen")
    assert frost.title == "Pakkanen – 2026-01-10"
    assert "-4.0 °C" in frost.body


def test_frost_threshold_is_inclusive() -> None:
    alerts = analyze_forecast(forecast(point(0, temperature=FROST_THRESHOLD_C)))

    assert any(alert.kind == "pakkanen" for alert in alerts)


def test_no_frost_alert_above_threshold() -> None:
    alerts = analyze_forecast(forecast(point(0, temperature=FROST_THRESHOLD_C + 0.1)))

    assert all(alert.kind != "pakkanen" for alert in alerts)


def test_snow_alert_sums_all_hours_and_reports_amount() -> None:
    alerts = analyze_forecast(
        forecast(point(0, snowfall=1.2), point(1, snowfall=0.8))
    )

    snow = next(alert for alert in alerts if alert.kind == "lumisade")
    assert "2.0 cm" in snow.body


def test_snow_threshold_is_inclusive() -> None:
    alerts = analyze_forecast(
        forecast(point(0, snowfall=SNOWFALL_THRESHOLD_CM))
    )

    assert any(alert.kind == "lumisade" for alert in alerts)


def test_snow_just_below_threshold_does_not_alert() -> None:
    alerts = analyze_forecast(
        forecast(point(0, snowfall=SNOWFALL_THRESHOLD_CM - 0.01))
    )

    assert all(alert.kind != "lumisade" for alert in alerts)


def test_snow_near_freezing_creates_slippery_risk() -> None:
    alerts = analyze_forecast(forecast(point(0, temperature=1.5, snowfall=0.2)))

    slippery = next(alert for alert in alerts if alert.kind == "liukkausriski")
    assert "lumisadetta" in slippery.body
    assert "ei tieto teiden todellisesta kunnosta" in slippery.body


def test_rain_slightly_above_zero_creates_slippery_risk() -> None:
    alerts = analyze_forecast(forecast(point(0, temperature=1.5, rain=0.5)))

    slippery = next(alert for alert in alerts if alert.kind == "liukkausriski")
    assert "vesisadetta 0.5 mm" in slippery.body


def test_rain_followed_by_freezing_temperature_creates_risk_with_timing() -> None:
    alerts = analyze_forecast(
        forecast(point(0, temperature=2, rain=0.6), point(4, temperature=-1))
    )

    slippery = next(alert for alert in alerts if alert.kind == "liukkausriski")
    assert "jonka jälkeen lämpötila laskee" in slippery.body


def test_rain_and_freeze_at_six_hour_boundary_creates_risk() -> None:
    alerts = analyze_forecast(
        forecast(point(0, temperature=4, rain=0.6), point(6, temperature=0))
    )

    assert any(alert.kind == "liukkausriski" for alert in alerts)


def test_rain_without_near_freezing_temperature_does_not_create_slippery_risk() -> None:
    alerts = analyze_forecast(forecast(point(0, temperature=8, rain=1.0)))

    assert all(alert.kind != "liukkausriski" for alert in alerts)


def test_rain_followed_by_freezing_after_six_hours_does_not_match_sequence_rule() -> None:
    alerts = analyze_forecast(
        forecast(point(0, temperature=4, rain=0.6), point(7, temperature=-1))
    )

    assert all(alert.kind != "liukkausriski" for alert in alerts)


def test_empty_forecast_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        analyze_forecast(Forecast(points=()))
