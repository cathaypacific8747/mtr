from rich import inspect, print
from datetime import datetime
import pandas as pd
import requests
import os
import matplotlib.pyplot as plt

definitions = {
    "weatherCode": {
        "50": "Sunny",
        "51": "Sunny Periods",
        "52": "Sunny Intervals",
        "53": "Sunny Periods with A Few Showers",
        "54": "Sunny Intervals with Showers",
        "60": "Cloudy",
        "61": "Overcast",
        "62": "Light Rain",
        "63": "Rain",
        "64": "Heavy Rain",
        "65": "Thunderstorms",
        "76": "Mainly Cloudly",
        "77": "Mainly Fine",
        "701": "Mainly Cloudly",
        "702": "Mainly Fine",
        "711": "Mainly Cloudly",
        "712": "Mainly Fine",
        "721": "Mainly Cloudly ",
        "722": "Mainly Fine",
        "741": "Mainly Cloudly",
        "742": "Mainly Fine",
        "751": "Mainly Cloudly",
        "752": "Mainly Fine"
    },
    "stationCode": {
        "CCH": "Cheung Chau",
        "HKA": "Chek Lap Kok",
        "HKO": "Hong Kong Observatory",
        "HKS": "Wong Chuk Hang",
        "JKB": "Tseung Kwan O",
        "LFS": "Lau Fau Shan",
        "PEN": "Peng Chau",
        "SEK": "Shek Kong",
        "SHA": "Sha Tin",
        "SKG": "Sai Kung",
        "TKL": "Ta Kwu Ling",
        "TPO": "Tai Po",
        "TUN": "Tuen Mun",
        "TY1": "Tsing Yi",
        "WGL": "Waglan Island",
        "SSH": "Sheung Shui",
        "TMS": "Tai Mo Shan",
        "TC": "Tate's Cairn",
    }
}

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
        
        plt.plot(self.hourlyForecast['ts'], self.hourlyForecast['temp'])
        plt.savefig(f'output/{self.modelTime}_{self.stationCode}_temp.jpg', dpi=600)
        plt.close()
        
        return self

    def parseDate(self, date: float or str) -> int:
        h = str(date)
        return int(datetime.timestamp(datetime(year=int(h[:4]), month=int(h[4:6]), day=int(h[6:8]), hour=int(h[8:10]), minute=int(h[10:12]), second=int(h[12:]))))

    def getWeatherDescription(self, weatherCode: float or str) -> str:
        return definitions['weatherCode'][str(weatherCode)] if str(weatherCode) in definitions['weatherCode'] else 'Unknown'

class HourlyForecast(Forecast):
    def __init__(self, data:dict):
        print(data)
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

def batchForecast():
    categorised_dfs = {}
    for station in definitions["stationCode"]:
        f = Forecast(stationCode=station)
        for h in f.hourlyForecast.columns.values:
            if h != 'ts':
                if h not in categorised_dfs:
                    categorised_dfs[h] = []
                categorised_dfs[h].append(f.hourlyForecast[["ts", h]].rename(columns={h: station}))
        
    for category in categorised_dfs:
        df = categorised_dfs[category][0]
        for station_df in categorised_dfs[category][1:]:
            df = df.merge(station_df, on='ts')
        
        if not os.path.exists('output'):
            os.mkdir('output')
        df.to_csv(f'output/all_{category}.csv')

if __name__ == '__main__':
    f = Forecast(stationCode='SHA')
    f.saveForecast()
    # batchForecast()