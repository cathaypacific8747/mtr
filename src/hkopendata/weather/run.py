import time
from dataclasses import asdict, dataclass
from itertools import chain
from pathlib import Path
from typing import Generator, TypedDict

import httpx
import orjson
import polars as pl
from tqdm import tqdm

from . import DATA_DIR
from .ocf import fetch_ocf
from .station import grid, stations

RUN_DIR = DATA_DIR / "runs"


async def start_run() -> None:
    run_id = int(time.time())

    base_dir = RUN_DIR / str(run_id)
    hourly_dir = base_dir / "hourly"
    hourly_dir.mkdir(parents=True, exist_ok=True)
    # daily_dir = base_dir / "daily"
    # daily_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        stations_all = []
        for station in tqdm(chain(grid(), stations())):
            ocf = await fetch_ocf(client, station.id)

            pl.DataFrame(ocf["HourlyWeatherForecast"]).write_parquet(
                hourly_dir / f"{station.id}.parquet"
            )
            # pl.DataFrame(ocf["DailyForecast"]).write_parquet(
            #     daily_dir / f"{station.id}.parquet"
            # )

            stations_all.append(
                {
                    **asdict(station),
                    "lat": ocf["Latitude"],
                    "lng": ocf["Longitude"],
                    "last_modified": ocf["LastModified"],
                    "model_time": ocf["ModelTime"],
                }
            )

        with open(base_dir / "stations.json", "wb") as f:
            f.write(orjson.dumps(stations_all, option=orjson.OPT_INDENT_2))


class Station(TypedDict):
    id: str
    backup: str | None
    urban: bool
    aws: bool
    grid: bool
    lat: float
    lng: float
    last_modified: int
    model_time: int


@dataclass
class Run:
    fp: Path

    def load_stations(self) -> list[Station]:
        with open(self.fp / "stations.json") as f:
            return orjson.loads(f.read())  # type: ignore


def runs() -> Generator[Run, None, None]:
    for run in (DATA_DIR / "runs").iterdir():
        if run.is_dir():
            yield Run(fp=run)


def plot() -> None:
    # def spatial_grid() -> npt.NDArray[np.float64]:
    #     return np.full((16, 15), np.nan)  # (lng, lat)

    import matplotlib.pyplot as plt

    plt.style.use("dark_background")

    HKO = (114.174637, 22.302219)
    DISTANCE_MAX = 1.2
    DISTANCE_MAX_STATION = 0.4

    for base_dir in runs():
        hourly_dir = base_dir.fp / "hourly"

        # arr = spatial_grid()
        for station in base_dir.load_stations():
            time, wind_speed = (
                pl.scan_parquet(hourly_dir / f"{station['id']}.parquet")
                .select("ForecastHour", "ForecastWindSpeed")
                .collect()
            )
            distance = (
                (HKO[0] - station["lng"]) ** 2 + (HKO[1] - station["lat"]) ** 2
            ) ** 0.5
            if not station["grid"] and station["aws"]:
                plt.plot(
                    time,
                    wind_speed,
                    label=station["id"],
                    lw=(DISTANCE_MAX_STATION - distance) / DISTANCE_MAX_STATION * 3,
                )
                continue
            if station["grid"]:
                plt.plot(
                    time,
                    wind_speed,
                    color="white",
                    alpha=(DISTANCE_MAX - distance) / DISTANCE_MAX * 0.1,
                )
                # i = int(station["id"][1:]) - 1
                # arr.flat[i] = df["ForecastWindSpeed"][5]

        # plt.imshow(arr, cmap="viridis")
        # plt.colorbar()
        plt.legend()
        plt.xticks(rotation=45)
        plt.show()
        plt.close()
        # break
