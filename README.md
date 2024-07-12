# hkopendata

This repo contains miscellaneous tools for analysing open geospatial data.

## weather

Ojective consensus forecast (OCF) weather predictions from the Hong Kong Observatory.

Wind Speed analysis for TC Nalgae:
![Analysis](src/weather/data/img/nalgae_wind.png)

Temp drop on 01 Dec 2022:
![Analysis](stc/weather/data/img/1dec_tempdrop.png)

### Note
- forecast: https://www.hko.gov.hk/en/wxinfo/awsgis/regional_weather_gis.html
- anemometer: https://maps.hko.gov.hk/ocf/index_e.html

- wind forecast at Kai Tak is inaccurate (Grid #153 is used instead)
- wind forecast at HKO is inaccurate (Star Ferry is used instead)
- wind forecast at Tai Po may be slightly inaccurate (Tai Po Kau is used instead)
- wind forecast at Sheung Shui removed due to no anemometers in that region