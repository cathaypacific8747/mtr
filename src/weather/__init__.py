import glob
import os
import re
import shutil
import time
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import pytz

from .api import AnemometerHistory, Forecast, get_station_detail
from .data import get_stations

plt.rcParams["font.family"] = "cmr10"
plt.rcParams["axes.formatter.use_mathtext"] = True
plt.style.use("dark_background")
plt.switch_backend("QtAgg")


def cleanup(delete: bool = False):
    for d in ["output", "output_anemometer"]:
        for f in os.listdir(d):
            fi = os.path.join(d, f)
            if os.path.isfile(fi):
                if delete:
                    os.remove(fi)
                else:
                    os.rename(fi, os.path.join(d, "dep", f))


def backup():
    if not os.path.exists("backup"):
        os.mkdir("backup")
    td = f"backup/{int(time.time())}"
    os.mkdir(td)
    for d in ["output", "output_anemometer"]:
        shutil.copytree(d, os.path.join(td, d))


def ts2str(ts: int):
    return datetime.fromtimestamp(ts, pytz.timezone("Asia/Hong_Kong")).strftime(
        "%d/%m %H:%M"
    )


def adj_graph(right=0.75):
    plt.legend(bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.subplots_adjust(left=0.1, right=right, bottom=0.1, top=0.9)
    plt.gcf().set_size_inches(16, 9)


###


def batch_forecast(typhoon_only: bool):
    categorised_dfs: dict[str, list[pd.DataFrame]] = {}
    last_mod = 0
    for s in get_stations():
        if typhoon_only and not s["typhoon"]:
            continue

        print("FORECAST |", s["name"])
        f = Forecast(station_code=s["id"])
        if f.last_modified > last_mod:
            last_mod = f.last_modified
        for h in f.hourly_forecast.columns.to_numpy():
            if h != "ts":
                if h not in categorised_dfs:
                    categorised_dfs[h] = []
                categorised_dfs[h].append(
                    f.hourly_forecast[["ts", h]].rename(columns={h: s["id"]})
                )

    for category in categorised_dfs:
        df = categorised_dfs[category][0]
        for station_df in categorised_dfs[category][1:]:
            df = df.merge(station_df, on="ts")

        if not os.path.exists("output"):
            os.mkdir("output")
        df.to_csv(f"output/{last_mod}_ALL_{category}.csv", index=False)


def batch_anemometer(typhoon_only: bool):
    tses: dict[int, dict[str, float]] = {}
    for s in get_stations():
        if typhoon_only and not s["typhoon"]:
            continue

        print("ANEMOMETER |", s["name"])
        h = AnemometerHistory(stationid=s["id"].lower())

        for _, row in h.data.iterrows():
            tses.setdefault(row["ts"], {}).update(
                {
                    f"{h.station_id}_windspeed": row["windSpeed"],
                    f"{h.station_id}_windDir": row["windDir"],
                }
            )

    df = pd.DataFrame(tses).T
    df.index.name = "ts"
    df = df.reindex(
        sorted(df.columns, key=lambda x: (x.split("_")[1], x.split("_")[0])), axis=1
    )
    df.to_csv(f"output_anemometer/{int(df.index.max())}_ALL_wind.csv")


def analyse_wind(typhoon_only: bool, filter: str | None = None):
    typhoon_stations = [s["id"] for s in get_stations() if s["typhoon"]]
    colours = {}
    df = None

    for f in glob.glob("output_anemometer/*_ALL_wind.csv"):
        dfr = pd.read_csv(f, index_col="ts")
        df1 = dfr[[col for col in dfr.columns if "windDir" not in col]]
        df = df1 if df is None else pd.concat([df, df1])

    assert df is not None
    df = df.sort_index()
    xmn, xmx = df.index.min() / 86400, df.index.max() / 86400

    for col in df.columns:
        if typhoon_only and col.split("_")[0] not in typhoon_stations:
            continue
        if filter and filter not in col:
            continue
        x, y = df.index / 86400, df[col]
        stationid = col.split("_")[0].lower()
        label = next(s["name"] for s in get_stations() if s["id"] == stationid)
        p = plt.plot(x, y, label=label)
        colours[stationid] = p[0].get_color()

    forecasts = sorted(glob.glob("output/*_ALL_windSpeed.csv"), reverse=True)
    for i, f in enumerate(forecasts):
        lw = 1 if len(forecasts) == 1 else 1 - ((i + 1) / len(forecasts)) * 0.8
        df = pd.read_csv(f, index_col="ts")
        forecast_time = int(f.split("_")[0].split("/")[-1])
        for col in df.columns:
            if typhoon_only and col.split("_")[0] not in typhoon_stations:
                continue
            if filter and filter not in col:
                continue
            x, y = df.index / 86400, df[col]
            station_name = next(s["name"] for s in get_stations() if s["id"] == col)
            plt.plot(
                x,
                y,
                label=f"{station_name} Forecast ({ts2str(forecast_time)})",
                color=colours[col],
                linewidth=lw,
            )
            plt.axvline(x=forecast_time / 86400, color=colours[col], linewidth=lw)

    plt.title("Wind Speed + Forecast")
    plt.xlabel("Time (HKT)")
    plt.ylabel("Wind Speed (km/h)")
    plt.gca().xaxis.set_major_formatter(
        mdates.DateFormatter("%d/%m\n%H:%M", tz=pytz.timezone("Asia/Hong_Kong"))
    )
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.axhline(y=64, color="red", linestyle="-")
    plt.axhline(y=41, color="orange", linestyle="-")
    plt.text(xmn, 64.5, "T8", color="red", fontsize=12)
    plt.text(xmn, 41.5, "T3", color="orange", fontsize=12)
    plt.xlim(xmn, xmx + 2)

    adj_graph()
    plt.savefig("analyse.png", dpi=600)
    plt.show()


def analyse_temp():
    forecasts = sorted(glob.glob("output/*_ALL_temp.csv"))
    for _, f in enumerate(forecasts):
        ts = int(re.compile(r"output/(\d+)_ALL_temp.csv").search(f).group(1))
        df = pd.read_csv(f, index_col="ts")
        th, mean, stdev = df.index / 86400, df.mean(axis=1), df.std(axis=1)
        for col in df.columns:
            plt.plot(th, df[col], color="grey", lw=0.1)
        plt.plot(th, mean, label=ts2str(ts), lw=2)
        plt.fill_between(th, mean - stdev, mean + stdev, alpha=0.2)

    plt.title("Average Temp Forecast")
    plt.xlabel("Time (HKT)")
    plt.ylabel("Temperature (°C)")
    plt.gca().xaxis.set_major_formatter(
        mdates.DateFormatter("%d/%m\n%H:%M", tz=pytz.timezone("Asia/Hong_Kong"))
    )
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=12))

    adj_graph(right=0.85)
    tsmin = (
        int(re.compile(r"output/(\d+)_ALL_temp.csv").search(forecasts[0]).group(1))
        / 86400
    )
    plt.xlim(tsmin, tsmin + 15)
    plt.savefig("analyse_temp.png", dpi=600)
    plt.show()


if __name__ == "__main__":
    backup()
    cleanup(delete=False)
    batch_forecast(typhoon_only=False)
    batch_anemometer(typhoon_only=False)

    analyse_wind(typhoon_only=False)
    # analyseTemp()
