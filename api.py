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

def get_station_detail(id, detail='name') -> str | None:
    for s in stations:
        if s['id'] == id:
            return s['name'] if detail == 'name' else s.get('an_id', s['id']) if detail == 'an_id' else None
    return None

with open('weathercodes.json', 'r') as f:
    weathercodes = json.load(f)

class Forecast():
    def __init__(self, stationCode):
        data = requests.get(f'https://maps.hko.gov.hk/ocf/dat/{stationCode.upper()}.xml').json()
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
        self.hourlyForecast.to_csv(f'output/{self.lastModified}_{self.stationCode}_hourly.csv', index=False)
        self.dailyForecast.to_csv(f'output/{self.lastModified}_{self.stationCode}_daily.csv', index=False)
        
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
        self.weather = self.getWeatherDescription(data.get('ForecastDailyWeather', None))

class AnemometerHistory():
    def __init__(self, stationid) -> None:
        data = requests.get(f"https://www.hko.gov.hk/wxinfo/awsgis/{get_station_detail(stationid, 'an_id')}_wd.csv").text
        
        self.stationid = stationid
        self.data = pd.read_csv(StringIO(data), header=1, names=['ts', 'windSpeed', 'windDir'])
        self.data['ts'] = self.data['ts'].apply(lambda x: int(datetime.timestamp(datetime.strptime(x, '%Y/%m/%d %H:%M'))))
        self.time = self.data['ts'].max()

    def saveHistory(self):
        if not os.path.exists('output_anemometer'):
            os.mkdir('output_anemometer')
        self.data.to_csv(f'output_anemometer/{self.time}_{self.stationid}_wind.csv', index=False)