from api import *
import matplotlib.dates as mdates
import pytz
import shutil
import time
from datetime import datetime
import glob
# from scipy.signal import savgol_filter
import pandas as pd

plt.rcParams['font.family'] = 'cmr10'
plt.rcParams['axes.formatter.use_mathtext'] = True
plt.style.use('dark_background')

def cleanup(delete:bool=False):
    for d in ['output', 'output_anemometer']:
        for f in os.listdir(d):
            fi = os.path.join(d, f)
            if os.path.isfile(fi):
                if delete:
                    os.remove(fi)
                else:
                    os.rename(fi, os.path.join(d, 'dep', f))

def backup():
    if not os.path.exists('backup'):
        os.mkdir('backup')
    td = f'backup/{int(time.time())}'
    os.mkdir(td)
    for d in ['output', 'output_anemometer']:
        shutil.copytree(d, os.path.join(td, d))

def batchForecast(typhoonOnly: bool):
    categorised_dfs = {}
    last_mod = 0
    for s in stations:
        if typhoonOnly and not s['typhoon']:
            continue

        print('FORECAST |', s['name'])
        f = Forecast(stationCode=s['id'])
        f.saveForecast()
        if f.lastModified > last_mod:
            last_mod = f.lastModified
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
        df.to_csv(f'output/{last_mod}_ALL_{category}.csv', index=False)

def batchAnemometer(typhoonOnly: bool):
    tses = {}
    for s in stations:
        if typhoonOnly and not s['typhoon']:
            continue

        print('ANEMOMETER |', s['name'])
        h = AnemometerHistory(stationid=s['id'].lower())
        h.saveHistory()

        for _, row in h.data.iterrows():
            tses.setdefault(row['ts'], {}).update({
                f'{h.stationid}_windspeed': row['windSpeed'],
                f'{h.stationid}_windDir': row['windDir']
            })
    
    df = pd.DataFrame(tses).T
    df.index.name = 'ts'
    df = df.reindex(sorted(df.columns, key=lambda x: (x.split('_')[1], x.split('_')[0])), axis=1)
    df.to_csv(f'output_anemometer/{int(df.index.max())}_ALL_wind.csv')

def analyse():
    colours = {}
    df = None

    for f in glob.glob('output_anemometer/*_ALL_wind.csv'):
        dfr = pd.read_csv(f, index_col='ts')
        df1 = dfr[[col for col in dfr.columns if 'windDir' not in col]]
        df = df1 if df is None else pd.concat([df, df1])

    df = df.sort_index()
    xmn, xmx = df.index.min()/86400, df.index.max()/86400

    for col in df.columns:
        # if 'hka' not in col: continue
        x, y = df.index / 86400, df[col]
        stationid = col.split('_')[0].lower()
        p = plt.plot(x, y, label=get_station_detail(stationid, 'name'))
        colours[stationid] = p[0].get_color()
        
        # xnew, ynew = savgol_filter((x, y), 20, 3)
        # plt.plot(xnew, ynew, label=col)
    
    forecasts = sorted(glob.glob('output/*_ALL_windSpeed.csv'), reverse=True)
    for i, f in enumerate(forecasts):
        lw = 1 - ((i+1) / len(forecasts)) * .8
        df = pd.read_csv(f, index_col='ts')
        forecastTime = int(f.split('_')[0].split('/')[-1])
        for col in df.columns:
            # if 'hka' not in col: continue
            x, y = df.index / 86400, df[col]
            plt.plot(x, y, label=f"{get_station_detail(col, 'name')} Forecast ({datetime.fromtimestamp(forecastTime, pytz.timezone('Asia/Hong_Kong')).strftime('%d/%m %H:%M')})", color=colours[col], linewidth=lw)
            plt.axvline(x=forecastTime/86400, color=colours[col], linewidth=lw)

    plt.title('Wind Speed + Forecast')
    plt.xlabel('Time (HKT)')
    plt.ylabel('Wind Speed (km/h)')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m\n%H:%M', tz=pytz.timezone('Asia/Hong_Kong')))
    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.axhline(y=64, color='red', linestyle='-')
    plt.axhline(y=41, color='orange', linestyle='-')
    plt.text(xmn, 64.5, 'T8', color='red', fontsize=12)
    plt.text(xmn, 41.5, 'T3', color='orange', fontsize=12)
    plt.xlim(xmn, xmx+2)
    # plt.xlim(xmn)

    plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left')
    plt.subplots_adjust(left=.1, right=.75, bottom=.1, top=.9)
    plt.gcf().set_size_inches(16, 9)
    plt.savefig('analyse.png', dpi=600)
    
    plt.show()

if __name__ == "__main__":
    # cleanup(delete=True)
    # backup()
    # batchForecast(typhoonOnly=False)
    # batchAnemometer(typhoonOnly=False)

    analyse()