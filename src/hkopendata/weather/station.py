from dataclasses import dataclass
from typing import Generator, TypedDict

import orjson

from . import DATA_DIR


class Stations(TypedDict):
    ALL_STATIONS: list[str]
    BACKUP_STATIONS: list[str]
    BACKUP_RULES: list[str]
    URBAN_STATIONS: list[str]
    AWS_STATIONS: list[str]


@dataclass
class GridCoordinates:
    lat: float
    lng: float

    @staticmethod
    def from_id(i: int) -> "GridCoordinates":
        (lat_offset, lng_offset) = divmod(i - 1, 16)
        return GridCoordinates(
            lat=round(23.2 - 0.1 * lat_offset, 1),
            lng=round(113.4 + 0.1 * lng_offset, 1),
        )


@dataclass
class Station:
    id: str
    backup: str | None
    urban: bool
    aws: bool
    grid: bool


def grid() -> Generator[Station, None, None]:
    for i in range(1, 241):
        yield Station(
            id=f"G{i}",
            backup=None,
            urban=False,
            aws=False,
            grid=True,
        )


def stations() -> Generator[Station, None, None]:
    """Transform original JavaScript representation to records."""
    with open(DATA_DIR / "station_ids.json") as f:
        stations: Stations = orjson.loads(f.read())  # type: ignore
    for station_id in stations["ALL_STATIONS"]:
        yield Station(
            id=station_id,
            backup=station_id if station_id in stations["BACKUP_STATIONS"] else None,
            urban=station_id in stations["URBAN_STATIONS"],
            aws=station_id in stations["AWS_STATIONS"],
            grid=False,
        )
