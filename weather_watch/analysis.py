"""Forecast rules for frost, snowfall, and slippery-condition risk."""

import logging
from datetime import timedelta

from .config import (
    FREEZE_AFTER_RAIN_HOURS,
    FREEZE_AFTER_RAIN_MAX_TEMP_C,
    FREEZING_POINT_C,
    FROST_THRESHOLD_C,
    LOCATION_NAME,
    NEAR_FREEZING_RAIN_MAX_C,
    NEAR_FREEZING_SNOW_MAX_C,
    SNOWFALL_RISK_THRESHOLD_CM,
    SNOWFALL_THRESHOLD_CM,
    WET_PRECIPITATION_THRESHOLD_MM,
)
from .models import Forecast, HourlyWeather, WeatherAlert

LOGGER = logging.getLogger(__name__)
OPEN_METEO_ATTRIBUTION = (
    "[Open-Meteo](https://open-meteo.com/) -sääennuste; "
    "ennustedata CC BY 4.0 -lisenssillä."
)


def _alert_date(point: HourlyWeather) -> str:
    return point.time.date().isoformat()


def _slippery_reasons(points: tuple[HourlyWeather, ...]) -> list[str]:
    reasons = []
    for index, point in enumerate(points):
        wet_mm = point.rain_mm + point.showers_mm
        has_wet_precipitation = wet_mm >= WET_PRECIPITATION_THRESHOLD_MM

        if (
            point.snowfall_cm >= SNOWFALL_RISK_THRESHOLD_CM
            and point.temperature_c <= NEAR_FREEZING_SNOW_MAX_C
        ):
            reasons.append(
                f"{point.time:%d.%m. klo %H}: lumisadetta {point.snowfall_cm:.1f} cm "
                f"ja lämpötila {point.temperature_c:.1f} °C"
            )

        if has_wet_precipitation and point.temperature_c <= NEAR_FREEZING_RAIN_MAX_C:
            reasons.append(
                f"{point.time:%d.%m. klo %H}: vesisadetta {wet_mm:.1f} mm "
                f"lämpötilassa {point.temperature_c:.1f} °C"
            )

        if (
            not has_wet_precipitation
            or not (
                FREEZING_POINT_C
                < point.temperature_c
                <= FREEZE_AFTER_RAIN_MAX_TEMP_C
            )
        ):
            continue

        freeze_deadline = point.time + timedelta(hours=FREEZE_AFTER_RAIN_HOURS)
        for later_point in points[index + 1 :]:
            if later_point.time > freeze_deadline:
                break
            if later_point.temperature_c <= FREEZING_POINT_C:
                reasons.append(
                    f"{point.time:%d.%m. klo %H}: vesisadetta {wet_mm:.1f} mm "
                    f"lämpötilassa {point.temperature_c:.1f} °C, jonka jälkeen "
                    f"lämpötila laskee {later_point.temperature_c:.1f} °C:een "
                    f"{later_point.time:%d.%m. klo %H} mennessä"
                )
                break

    return list(dict.fromkeys(reasons))


def analyze_forecast(forecast: Forecast) -> list[WeatherAlert]:
    """Return at most one alert of each type for the supplied 24-hour forecast."""
    if not forecast.points:
        raise ValueError("Forecast must contain at least one hourly point")

    alerts = []
    points = forecast.points
    period = f"{points[0].time:%d.%m. klo %H}–{points[-1].time:%d.%m. klo %H}"

    coldest = min(points, key=lambda point: point.temperature_c)
    if coldest.temperature_c <= FROST_THRESHOLD_C:
        alerts.append(
            WeatherAlert(
                kind="pakkanen",
                title=f"Pakkanen – {_alert_date(coldest)}",
                body=(
                    f"{LOCATION_NAME}: seuraavan vuorokauden alin ennustettu lämpötila "
                    f"on {coldest.temperature_c:.1f} °C ({coldest.time:%d.%m. klo %H}). "
                    f"Varoitusraja on {FROST_THRESHOLD_C:.1f} °C. "
                    f"Ennustejakso: {period} Suomen aikaa.\n\n{OPEN_METEO_ATTRIBUTION}"
                ),
            )
        )
        LOGGER.info("Pakkasvaroitus: alin lämpötila %.1f °C", coldest.temperature_c)
    else:
        LOGGER.info(
            "Ei pakkasvaroitusta: alin lämpötila %.1f °C (raja %.1f °C)",
            coldest.temperature_c,
            FROST_THRESHOLD_C,
        )

    snowfall_total = sum(point.snowfall_cm for point in points)
    if snowfall_total >= SNOWFALL_THRESHOLD_CM:
        alerts.append(
            WeatherAlert(
                kind="lumisade",
                title=f"Lumisade – {points[0].time.date().isoformat()}",
                body=(
                    f"{LOCATION_NAME}: seuraavalle 24 tunnille ennustetaan yhteensä "
                    f"{snowfall_total:.1f} cm lunta (varoitusraja "
                    f"{SNOWFALL_THRESHOLD_CM:.1f} cm). Ennustejakso: {period} "
                    f"Suomen aikaa.\n\n{OPEN_METEO_ATTRIBUTION}"
                ),
            )
        )
        LOGGER.info("Lumisadevaroitus: ennustettu määrä %.1f cm", snowfall_total)
    else:
        LOGGER.info(
            "Ei lumisadevaroitusta: ennustettu määrä %.1f cm (raja %.1f cm)",
            snowfall_total,
            SNOWFALL_THRESHOLD_CM,
        )

    slippery_reasons = _slippery_reasons(points)
    if slippery_reasons:
        reason_text = "\n".join(f"- {reason}" for reason in slippery_reasons)
        alerts.append(
            WeatherAlert(
                kind="liukkausriski",
                title=f"Liukkausriski – {points[0].time.date().isoformat()}",
                body=(
                    f"{LOCATION_NAME}: sääennusteessa on olosuhteita, jotka voivat "
                    "lisätä liukkauden riskiä:\n"
                    f"{reason_text}\n\n"
                    "Kyseessä on sääennusteeseen perustuva riskinarvio, ei tieto "
                    "teiden todellisesta kunnosta. Liukkautta voi esiintyä myös "
                    "hieman nollan yläpuolella, eikä ilman lämpötila yksin kerro "
                    "tien pinnan lämpötilaa. Tarkista paikalliset olosuhteet.\n\n"
                    f"{OPEN_METEO_ATTRIBUTION}"
                ),
            )
        )
        LOGGER.info("Liukkausriski havaittu: %s", "; ".join(slippery_reasons))
    else:
        LOGGER.info("Ei liukkausriskin tunnusmerkit täyttäviä sääolosuhteita")

    return alerts
