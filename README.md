# hkopendata

This repo contains miscellaneous tools for downloading and analysing open geospatial data in Hong Kong.

It also serves as a monorepo of my old toy projects. They are largely written in good ol' jquery and plain JS. Links to github pages:

- [`old/btehk-3dmap`](https://cathaypacific8747.github.io/hkopendata/old/btehk-3dmap/): A 3D map/visualisation of Hong Kong aimed to help builders of the BuildTheEarth HK Community.
- [`old/mtr`](https://cathaypacific8747.github.io/hkopendata/old/mtr/): Check MTR times easier.
- [`old/cky-bus`](https://cathaypacific8747.github.io/hkopendata/old/cky-bus/): Check KMB bus times at my secondary school.

These still work, but are pretty cringe and will be rewritten in the future.

Installation (CLI):

```sh
cd hkopendata
uv tool install "https://github.com/cathaypacific8747/hkopendata[cli]"
hkopendata --help
```

Installation (library):

```sh
uv add https://github.com/cathaypacific8747/hkopendata
```

Development:

```sh
git clone https://github.com/cathaypacific8747/hkopendata
uv sync --all-extras --all-groups
uv tool install ".[cli]" --editable
```

## features

### hydro

Download raster tiles from the Hong Kong Hydrographic Office, Marine Department:

![demo](docs/assets/hydro_demo.webp)

### weather

Objective consensus forecast (OCF) weather predictions from the Hong Kong Observatory.

- forecast: https://www.hko.gov.hk/en/wxinfo/awsgis/regional_weather_gis.html
- anemometer: https://maps.hko.gov.hk/ocf/index_e.html

Wind Speed analysis for TC Nalgae:
![Analysis](docs/assets/nalgae_wind.png)

Temp drop on 01 Dec 2022:
![Analysis](docs/assets/1dec_tempdrop.png)