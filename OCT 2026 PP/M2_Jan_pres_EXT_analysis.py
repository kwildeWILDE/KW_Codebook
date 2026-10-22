#import necessary libraries
from webbrowser import get

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd 
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse, Patch
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min, multivariate_normal
import os
import glob 
import re
import seaborn as sns

##########################################################
########### PULLING THE M2 DATA #####
dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_pub_Jan31_Present_Datapull.xlsx"

#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)
# print(ds_m2.head())

##### Convert to UTC ### 
## The M2 timestamps are in MST (UTC-7) all year (no daylight saving shift; verified
## against the Z02 lidar wind speed), so UTC = MST + 7 h.
ds_m2['DS_time'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + ds_m2['MST'].astype(str))
ds_m2['UTC_time'] = ds_m2['DS_time'] + pd.Timedelta(hours=7)

# print("M2 data loaded and converted to UTC.", 
#       ds_m2['UTC_time'].astype(str) )

####### Getting data quality mesh for the M2 dataset 
status_code = ds_m2['EFM Status Code'] 
# try to create a mask for good quality code 
#that skips the poor quality data (EFM Status Code > 10)
good_quality_mask = ds_m2['EFM Status Code'] <= 10
ds_m2 = ds_m2.loc[good_quality_mask]

print("M2 data filtered for good quality.")
# print(ds_m2.head())
########################################################
## Try to split the M2 data into periods of when the sun is down (nighttime) and up (daytime) at moutain time
#define daytime and nighttime based on sunrise and sunset times in MST
#for simplicity, assume sunrise at 6:00 MST and sunset at 18:00 MST

#frist make the time readable by extracting the hour from the MST column
#Convert MST into an apporite data format for plotting
ds_m2['datetime'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + ds_m2['MST'].astype(str))
time = ds_m2['datetime']

#now split the data into daytime and nighttime based on the hour extracted from MST
ds_m2['hour'] = ds_m2['datetime'].dt.hour
ds_m2['is_daytime'] = (ds_m2['hour'] >= 6) & (ds_m2['hour'] < 18)
ds_m2['is_nighttime'] = ~ds_m2['is_daytime']
print("M2 data split into daytime and nighttime based on MST hour.")
print(ds_m2[['MST', 'hour', 'is_daytime', 'is_nighttime']].head())

# Okay now the we can split the M2 into day time and night time regimes 
# We can create daytime and night time varaibles for on a month to month basis (FEB - Oct)
ds_m2['month'] = ds_m2['datetime'].dt.month
for month in range(2, 11):  # FEB (2) to OCT (10)
    ds_m2.loc[ds_m2['month'] == month, 'is_daytime_month'] = ds_m2['is_daytime']
    ds_m2.loc[ds_m2['month'] == month, 'is_nighttime_month'] = ds_m2['is_nighttime']
    print(f"Month {month} daytime and nighttime flags created.")
    print(ds_m2.loc[ds_m2['month'] == month, ['month', 'is_daytime_month', 'is_nighttime_month']].head())
    print()  # Add a blank line for readability between months

# Now pull the varaibles of temperature and wind speed at heights 2m and 50m 
m2_tempt_2m = ds_m2['Temperature @ 2m [deg C]']
m2_tempt_50m = ds_m2['Temperature @ 50m [deg C]']

m2_wind_2m = ds_m2['Avg Wind Speed @ 2m [m/s]']
m2_wind_50m = ds_m2['Avg Wind Speed @ 50m [m/s]']

#Making a Bivariate plot Kernerl Density Estimation (KDE) 2D PDF plot for temperature and wind speed at 2m and 50m
# on a month to month basis (FEB - OCT) for with separate daytime and nighttime regimes

#colors for the representive height
colors = {
    '2m': 'blue',
    '50m': 'green'
}

#physical limits: no wind speeds below 0 m/s and no temperatures below -23 C
MIN_TEMP = -23
MIN_WIND = 0

# Bivariate (2D) KDE joint PDF of wind speed and temperature, one figure per month (FEB - OCT), 2m and 50m in separate subplots
height_data = {
    '2m': (m2_wind_2m, m2_tempt_2m, 'b'),
    '50m': (m2_wind_50m, m2_tempt_50m, 'g'),
}

# for month in range(2, 11):
#     month_mask = (ds_m2['month'] == month).values
#     day_mask = ds_m2['is_daytime'].values.astype(bool)
#     #rows = height, columns = daytime / nighttime
#     fig, axes = plt.subplots(2, 2, figsize=(14, 12))

#     for row, (label, (wind_all, temp_all, color)) in enumerate(height_data.items()):
#         for col, (regime, regime_mask) in enumerate([('Daytime', day_mask), ('Nighttime', ~day_mask)]):
#             ax = axes[row, col]
#             sel = month_mask & regime_mask
#             wind_sp = np.asarray(wind_all)[sel].ravel()
#             temp = np.asarray(temp_all)[sel].ravel()
#             valid = ~(np.isnan(wind_sp) | np.isnan(temp)) & (wind_sp >= MIN_WIND) & (temp >= MIN_TEMP)
#             wind_sp, temp = wind_sp[valid], temp[valid]

#             ax.set_xlabel(f'Wind Speed @ {label} [m/s]')
#             ax.set_ylabel(f'Temperature @ {label} [deg C]')
#             ax.grid(True, linestyle='--', alpha=0.5)
#             if wind_sp.size < 10:
#                 ax.set_title(f'{label} {regime} (n={wind_sp.size}) - not enough data', fontsize=10)
#                 continue

#             # 2D KDE: non-parametric joint PDF, so multiple modes are preserved instead of forced into one Gaussian
#             kde = gaussian_kde(np.vstack([wind_sp, temp]))
#             x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
#             y = np.linspace(temp.min(), temp.max(), 100)
#             X, Y = np.meshgrid(x, y)
#             Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape) #evaluate the KDE joint PDF at each grid point

#             cf = ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
#             #small, faint scatter drawn first so the contour lines sit on top and stay visible
#             ax.scatter(wind_sp, temp, s=6, c=color, edgecolor='none', alpha=0.3, zorder=2)
#             #bold black contour lines with a white halo, labeled with density values
#             halo = ax.contour(X, Y, Z, levels=8, colors='white', linewidths=3.5, zorder=3)
#             cl = ax.contour(X, Y, Z, levels=halo.levels, colors='black', linewidths=1.6, zorder=4)
#             ax.clabel(cl, fmt='%.3f', fontsize=7)
#             fig.colorbar(cf, ax=ax, label='Density')
#             ax.set_title(f'KDE Joint PDF @ {label} {regime} (n={wind_sp.size})', fontsize=10)

#     fig.suptitle(f'Bivariate KDE Joint PDF of Wind Speed and Temperature for month {month}, 2026')
#     #add space for the suptitle so it doesn't overlap with subplots
#     plt.tight_layout(rect=[0, 0, 1, 0.95])
#     fig.subplots_adjust(hspace=0.5, wspace=0.3)
#     plt.show()


########## End of KDE Day and Night Analysis ##########
#From the plots above we can see that there are scatter points that lie outside the most outer density contour, 
# indicating that those points are outliers or extreme values not captured by the main density distribution.

# create a month to month time series of wind speed and temperature for the respective heights and day and night regimes
#while also highlighting any extreme values or outliers that fall outside the main density distribution

time_series_data = {
    '2m': (m2_wind_2m, m2_tempt_2m, 'b'),
    '50m': (m2_wind_50m, m2_tempt_50m, 'g'),
}

#Outliers = points in the lowest 5% of the bivariate KDE joint density (outside the outer contour),
#found separately for each month, height and day/night regime to match the KDE plots above
OUTLIER_PCT = 5
WIND_COLOR, TEMP_COLOR = 'tab:blue', 'tab:red'
dt_all = ds_m2['datetime'].values
day_all = ds_m2['is_daytime'].values.astype(bool)

def kde_outlier_flags(wind_sp, temp):
    flags = np.zeros(wind_sp.size, dtype=bool)
    if wind_sp.size < 10:
        return flags
    dens = gaussian_kde(np.vstack([wind_sp, temp]))(np.vstack([wind_sp, temp]))
    return dens <= np.percentile(dens, OUTLIER_PCT)

for month in range(2, 11):
    month_mask = (ds_m2['month'] == month).values
    if not month_mask.any():
        continue
    fig, axes = plt.subplots(2, 1, figsize=(15, 9), sharex=True)

    t_month = pd.DatetimeIndex(dt_all[month_mask])
    start = t_month.min().normalize()
    end = t_month.max().normalize() + pd.Timedelta(days=1)

    for ax, (label, (wind_all, temp_all, _)) in zip(axes, time_series_data.items()):
        wind = np.asarray(wind_all, dtype=float)
        temp = np.asarray(temp_all, dtype=float)
        valid = month_mask & ~(np.isnan(wind) | np.isnan(temp)) & (wind >= MIN_WIND) & (temp >= MIN_TEMP)

        #night = light grey background (18:00-06:00 MST), day stays white
        for d in pd.date_range(start - pd.Timedelta(days=1), end, freq='D'):
            ax.axvspan(d + pd.Timedelta(hours=18), d + pd.Timedelta(hours=30), color='lightgrey', alpha=0.6, lw=0, zorder=0)

        outlier = np.zeros(len(ds_m2), dtype=bool)
        for regime_mask in (day_all, ~day_all):
            idx = np.where(valid & regime_mask)[0]
            outlier[idx] = kde_outlier_flags(wind[idx], temp[idx])

        t = dt_all[valid]
        ax2 = ax.twinx()
        ax.plot(t, wind[valid], color=WIND_COLOR, lw=0.7, zorder=2, label='Wind speed')
        ax2.plot(t, temp[valid], color=TEMP_COLOR, lw=0.7, zorder=2, label='Temperature')
        out = outlier & valid
        ax.scatter(dt_all[out], wind[out], s=25, color='yellow', edgecolor='k', linewidth=0.5, zorder=4, label='Wind outlier')
        ax2.scatter(dt_all[out], temp[out], s=25, color='yellow', edgecolor='k', linewidth=0.5, marker='s', zorder=4, label='Temp outlier')

        ax.set_ylabel('Wind Speed [m/s]', color=WIND_COLOR)
        ax2.set_ylabel('Temperature [deg C]', color=TEMP_COLOR)
        ax.set_title(f'{label} (outliers: n={out.sum()})', fontsize=10)
        ax.set_xlim(start, end)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc='upper right', fontsize=8, ncol=4)

    axes[-1].set_xlabel('Time (MST)')
    fig.suptitle(f'Wind Speed and Temperature Time Series for month {month} (grey = night, white = day)')
    plt.tight_layout()
    fig.subplots_adjust(hspace=0.3)
    plt.show()

########## End of Time Series Outlier Analysis ##########
