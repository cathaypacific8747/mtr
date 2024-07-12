from pathlib import Path
from typing import Any

import orjson

DATA_DIR = Path(__file__).parent


def get_stations() -> dict[Any, Any]:
    with open(DATA_DIR / "stations.json") as f:
        return orjson.loads(f.read())


def get_weather_codes() -> dict[Any, Any]:
    with open(DATA_DIR / "weather_codes.json") as f:
        return orjson.loads(f.read())
