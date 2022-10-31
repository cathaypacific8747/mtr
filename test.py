from rich import inspect, print
from datetime import datetime
import pandas as pd
import requests
import os
import matplotlib.pyplot as plt
import json
from io import StringIO

with open('stations.json', 'r') as f:
    stations = json.load(f)

with open('weathercodes.json', 'r') as f:
    weathercodes = json.load(f)

class Forecast():
    def __init__(self, stationCode):
        data = requests.get(f'https://maps.hko.gov.hk/ocf/dat/{stationCode}.xml').json()
        self.stationCode = stationCode
        self.lastModified = self.parseDate(data['LastModified'])
        self.lat = data['Latitude']
        self.lng = data['Longitude']
        self.nearestStation = data['NearestStationCode'] if 'NearestStationCode' in data else stationCode
        self.modelTime = self.parseDate(str(data['ModelTime']) + '0000')
        self.hourlyForecast = pd.DataFrame([vars(HourlyForecast(f)) for f in data['HourlyWeatherForecast']])
        self.dailyForecast = pd.DataFrame([vars(DailyForecast(f)) for f in data['DailyForecast']])

    def saveForecast(self):
        if not os.path.exists('output'):
            os.mkdir('output')
        self.hourlyForecast.to_csv(f'output/{self.modelTime}_{self.stationCode}_hourly.csv')
        self.dailyForecast.to_csv(f'output/{self.modelTime}_{self.stationCode}_daily.csv')
        
        return self

    def parseDate(self, date: float or str) -> int:
        h = str(date)
        return int(datetime.timestamp(datetime(year=int(h[:4]), month=int(h[4:6]), day=int(h[6:8]), hour=int(h[8:10]), minute=int(h[10:12]), second=int(h[12:]))))

    def getWeatherDescription(self, weatherCode: float or str) -> str:
        return weathercodes[str(weatherCode)] if str(weatherCode) in weathercodes else 'Unknown'

class HourlyForecast(Forecast):
    def __init__(self, data:dict):
        self.ts = self.parseDate(data['ForecastHour'] + '0000')
        self.rh = data['ForecastRelativeHumidity'] if 'ForecastRelativeHumidity' in data else None
        self.temp = data['ForecastTemperature'] if 'ForecastTemperature' in data else None
        self.weather = self.getWeatherDescription(data['ForecastWeather']) if 'ForecastWeather' in data else None
        self.windDir = data['ForecastWindDirection'] if 'ForecastWindDirection' in data else None
        self.windSpeed = data['ForecastWindSpeed'] if 'ForecastWindSpeed' in data else None

class DailyForecast(Forecast):
    def __init__(self, data:dict):
        self.ts = self.parseDate(data['ForecastDate'] + '000000')
        self.chanceOfRain = 0 if '< 10' in data['ForecastChanceOfRain'] else int(data['ForecastChanceOfRain'].replace('%', '')) / 100
        self.weather = self.getWeatherDescription(data['ForecastDailyWeather'])

def batchForecast(typhoon: bool):
    categorised_dfs = {}
    model_time = 0
    for s in stations:
        if typhoon and not s['typhoon']:
            continue

        f = Forecast(stationCode=s['id'])
        f.saveForecast()
        model_time = f.modelTime
        for h in f.hourlyForecast.columns.values:
            if h != 'ts':
                if h not in categorised_dfs:
                    categorised_dfs[h] = []
                categorised_dfs[h].append(f.hourlyForecast[["ts", h]].rename(columns={h: s['id']}))
        
    for category in categorised_dfs:
        df = categorised_dfs[category][0]
        for station_df in categorised_dfs[category][1:]:
            df = df.merge(station_df, on='ts')
        
        if not os.path.exists('output'):
            os.mkdir('output')
        df.to_csv(f'output/{model_time}_ALL_{category}.csv')

class AnemometerHistory():
    def __init__(self, stationCode) -> None:
        data = requests.get(f"https://www.hko.gov.hk/wxinfo/awsgis/{stationCode}_wd.csv").text
        
        self.stationCode = stationCode
        self.data = pd.read_csv(StringIO(data), header=1, names=['ts', 'windSpeed', 'windDir'])
        self.data['ts'] = self.data['ts'].apply(lambda x: int(datetime.timestamp(datetime.strptime(x, '%Y/%m/%d %H:%M'))))

    def saveHistory(self):
        if not os.path.exists('output_anemometer'):
            os.mkdir('output_anemometer')
        self.data.to_csv(f'output_anemometer/{self.stationCode}_wind.csv', index=False)

def batchAnemometer(typhoon: bool):
    for s in stations:
        if typhoon and not s['typhoon']:
            continue

        h = AnemometerHistory(stationCode=s.get('an_id', s['id']).lower())
        h.saveHistory()


if __name__ == '__main__':
    # f = Forecast(stationCode='WGL')
    # f.saveForecast()
    batchForecast(typhoon=True)
    batchAnemometer(typhoon=True)