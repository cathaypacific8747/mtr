# hkopendata

This repo contains miscellaneous tools for downloading and analysing Hong Kong geospatial data.

```sh
uv sync
```

## hydro

Raster tiles from the Hong Kong Hydrographic Office, Marine Department.

![demo](src/hkopendata/hydro/data/img/demo.webp)

## weather

Ojective consensus forecast (OCF) weather predictions from the Hong Kong Observatory.

- forecast: https://www.hko.gov.hk/en/wxinfo/awsgis/regional_weather_gis.html
- anemometer: https://maps.hko.gov.hk/ocf/index_e.html

Wind Speed analysis for TC Nalgae:
![Analysis](src/hkopendata/weather/data/img/nalgae_wind.png)

Temp drop on 01 Dec 2022:
![Analysis](src/hkopendata/weather/data/img/1dec_tempdrop.png)

```py
uv run python3 -m src.hkopendata.weather
```