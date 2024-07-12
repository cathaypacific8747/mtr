from pathlib import Path
from typing import NotRequired, TypedDict

import orjson

DATA_DIR = Path(__file__).parent


class Station(TypedDict):
    id: str
    typhoon: bool
    name: str
    an_id: NotRequired[str]


def get_stations() -> list[Station]:
    with open(DATA_DIR / "stations.json") as f:
        return orjson.loads(f.read())


def get_weather_codes() -> dict[str, str]:
    with open(DATA_DIR / "weather_codes.json") as f:
        return orjson.loads(f.read())
