from __future__ import annotations

import httpx
from typing_extensions import NotRequired, TypedDict


async def fetch_ocf(client: httpx.AsyncClient, station_id: str) -> OCF:
    url = f"https://maps.weather.gov.hk/ocf/dat/{station_id}.xml"
    response = await client.get(url)
    response.raise_for_status()
    return response.json()  # type: ignore


class OCF(TypedDict):
    LastModified: int
    StationCode: str
    Latitude: float
    Longitude: float
    ModelTime: int
    DailyForecast: list[DailyForecast]
    HourlyWeatherForecast: list[HourlyWeatherForecast]


class DailyForecast(TypedDict):
    ForecastDate: str
    ForecastChanceOfRain: str
    ForecastDailyWeather: int
    ForecastMaximumTemperature: float
    ForecastMinimumTemperature: float


class HourlyWeatherForecast(TypedDict):
    ForecastHour: str
    ForecastRelativeHumidity: NotRequired[float]
    ForecastTemperature: NotRequired[float]
    ForecastWindDirection: NotRequired[float]
    ForecastWindSpeed: NotRequired[float]
    ForecastWeather: NotRequired[int]
