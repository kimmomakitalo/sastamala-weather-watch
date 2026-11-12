"""Typed data structures used by the forecast and alert logic."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HourlyWeather:
    time: datetime
    temperature_c: float
    rain_mm: float
    showers_mm: float
    snowfall_cm: float


@dataclass(frozen=True)
class Forecast:
    points: tuple[HourlyWeather, ...]


@dataclass(frozen=True)
class WeatherAlert:
    kind: str
    title: str
    body: str
