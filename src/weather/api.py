import os
from datetime import datetime, timedelta, timezone
from io import StringIO

import httpx
import pandas as pd

from .data import get_stations, get_weather_codes


def get_station_detail(id: str, detail="name") -> str | None:
    for s in get_stations():
        if s["id"] == id:
            return (
                s["name"]
                if detail == "name"
                else s.get("an_id", s["id"])
                if detail == "an_id"
                else None
            )
    return None


class Forecast:
    def __init__(self, station_code):
        data = httpx.get(
            f"https://maps.hko.gov.hk/ocf/dat/{station_code.upper()}.json"
        ).json()
        self.station_code = station_code
        self.last_modified = self.parse_date(data["LastModified"])
        self.lat = data["Latitude"]
        self.lng = data["Longitude"]
        self.nearest_station = (
            data["NearestStationCode"] if "NearestStationCode" in data else station_code
        )
        self.model_time = self.parse_date(str(data["ModelTime"]) + "0000")
        self.hourly_forecast = pd.DataFrame(
            [vars(HourlyForecast(f)) for f in data["HourlyWeatherForecast"]]
        )
        self.dailyForecast = pd.DataFrame(
            [vars(DailyForecast(f)) for f in data["DailyForecast"]]
        )

    def save_forecast(self):
        if not os.path.exists("output"):
            os.mkdir("output")
        self.hourly_forecast.to_csv(
            f"output/{self.last_modified}_{self.station_code}_hourly.csv", index=False
        )
        self.dailyForecast.to_csv(
            f"output/{self.last_modified}_{self.station_code}_daily.csv", index=False
        )

        return self

    def parse_date(self, date: float | str) -> int:
        h = str(date)
        return int(
            datetime.timestamp(
                datetime(
                    year=int(h[:4]),
                    month=int(h[4:6]),
                    day=int(h[6:8]),
                    hour=int(h[8:10]),
                    minute=int(h[10:12]),
                    second=int(h[12:]),
                    tzinfo=timezone(timedelta(hours=8)),
                )
            )
        )

    def get_weather_description(self, weather_code: float | str) -> str:
        weathercodes = get_weather_codes()
        return (
            weathercodes[str(weather_code)]
            if str(weather_code) in weathercodes
            else "Unknown"
        )


class HourlyForecast(Forecast):
    def __init__(self, data: dict):
        self.ts = self.parse_date(data["ForecastHour"] + "0000")
        self.rh = (
            data["ForecastRelativeHumidity"]
            if "ForecastRelativeHumidity" in data
            else None
        )
        self.temp = (
            data["ForecastTemperature"] if "ForecastTemperature" in data else None
        )
        self.weather = (
            self.get_weather_description(data["ForecastWeather"])
            if "ForecastWeather" in data
            else None
        )
        self.wind_dir = (
            data["ForecastWindDirection"] if "ForecastWindDirection" in data else None
        )
        self.wind_speed = (
            data["ForecastWindSpeed"] if "ForecastWindSpeed" in data else None
        )


class DailyForecast(Forecast):
    def __init__(self, data: dict):
        self.ts = self.parse_date(data["ForecastDate"] + "000000")
        self.chance_of_rain = (
            0
            if "< 10" in data["ForecastChanceOfRain"]
            else int(data["ForecastChanceOfRain"].replace("%", "")) / 100
        )
        self.weather = self.get_weather_description(
            data.get("ForecastDailyWeather", None)
        )


class AnemometerHistory:
    def __init__(self, stationid: str) -> None:
        station_id = next(s["an_id"] for s in get_stations())
        data = httpx.get(
            f"https://www.hko.gov.hk/wxinfo/awsgis/{station_id}_wd.csv"
        ).text

        self.station_id = stationid
        self.data = pd.read_csv(
            StringIO(data), header=1, names=["ts", "windSpeed", "windDir"]
        )
        self.data["ts"] = self.data["ts"].apply(
            lambda x: int(
                datetime.timestamp(
                    datetime.strptime(x, "%Y/%m/%d %H:%M").replace(
                        tzinfo=timezone(timedelta(hours=8))
                    )
                )
            )
        )
        self.time = self.data["ts"].max()

    def save_history(self):
        if not os.path.exists("output_anemometer"):
            os.mkdir("output_anemometer")
        self.data.to_csv(
            f"output_anemometer/{self.time}_{self.station_id}_wind.csv", index=False
        )
