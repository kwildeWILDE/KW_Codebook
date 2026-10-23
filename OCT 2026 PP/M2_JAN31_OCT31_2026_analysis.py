#import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import os
import re 
import glob
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min, multivariate_normal
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse, Patch
from windrose import WindroseAxes

#############################################
#Pull the Full M2 data from Jan 31 to Oct 17, 2026 

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

print(ds_m2.head())

#Convert MST into an apporite data format for plotting
ds_m2['datetime'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + ds_m2['MST'].astype(str))
time = ds_m2['datetime']


#from looking over the plot and the excel data there are varibles that have been recorded as "-99999"
#replace these with NaN for proper analysis
ds_m2 = ds_m2.replace(-99999, np.nan)

# ^^^^^ New ds to use that skips the -99999 values

#vairbles for temperature at different heights
temp2 = ds_m2['Temperature @ 2m [deg C]']
temp50 = ds_m2['Temperature @ 50m [deg C]']
temp80 = ds_m2['Temperature @ 80m [deg C]']

#varibles for wind speed at different heights
wind_speed2 = ds_m2['Avg Wind Speed @ 2m [m/s]']
wind_speed5 = ds_m2['Avg Wind Speed @ 5m [m/s]']
wind_speed10 = ds_m2['Avg Wind Speed @ 10m [m/s]']
wind_speed20 = ds_m2['Avg Wind Speed @ 20m [m/s]']
wind_speed50 = ds_m2['Avg Wind Speed @ 50m [m/s]']
wind_speed80 = ds_m2['Avg Wind Speed @ 80m [m/s]']


# variables for wind direction at different heights
wind_dir2 = ds_m2['Avg Wind Direction @ 2m [deg]']
wind_dir5 = ds_m2['Avg Wind Direction @ 5m [deg]']
wind_dir10 = ds_m2['Avg Wind Direction @ 10m [deg]']
wind_dir20 = ds_m2['Avg Wind Direction @ 20m [deg]']
wind_dir50 = ds_m2['Avg Wind Direction @ 50m [deg]']
wind_dir80 = ds_m2['Avg Wind Direction @ 80m [deg]']

#Flat (stuck-sensor) values: a run of identical consecutive readings is not real wind variability.
#Find runs on the full series (so runs crossing a month boundary are caught) and mask them as NaN.
MIN_FLAT_RUN = 6  # consecutive identical samples treated as flat; adjust to the M2 sampling interval

def mask_flat_runs(series, min_run=MIN_FLAT_RUN):
    run_id = (series != series.shift()).cumsum()
    run_len = series.groupby(run_id).transform('size')
    return series.mask((run_len >= min_run) & series.notna())

wind_speed10_clean = mask_flat_runs(wind_speed10)
wind_speed50_clean = mask_flat_runs(wind_speed50)
wind_speed80_clean = mask_flat_runs(wind_speed80)
wind_dir50_clean = mask_flat_runs(wind_dir50)  # stuck direction readings (e.g. repeated 0 deg)
wind_dir80_clean = mask_flat_runs(wind_dir80)
for month in range(2, 11):
    n_flat = (wind_speed10[time.dt.month == month].notna() & wind_speed10_clean[time.dt.month == month].isna()).sum()
    print(f"Month {month}: removed {n_flat} flat wind speed samples")

# create a month to month (Feb to Oct 2026) frequency hitogram with wibull fit line for wind speed at 10 m
# for month in range(2, 11):
#     wind_speed_month = wind_speed10_clean[time.dt.month == month].dropna()
#     #Weibull needs positive values; calm (0 m/s) samples are excluded from the fit
#     wind_speed_month = wind_speed_month[wind_speed_month > 0]
#     if len(wind_speed_month) == 0:
#         continue
#     plt.figure(figsize=(10, 6))
#     plt.hist(wind_speed_month, bins=20, density=True, alpha=0.6, color='b', label='Wind Speed Frequency')
#     # Fit a Weibull distribution
#     params = weibull_min.fit(wind_speed_month, floc=0)
#     x = np.linspace(0, wind_speed_month.max(), 100)
#     plt.plot(x, weibull_min.pdf(x, *params), 'r-', lw=2, label='Weibull Fit')
#     plt.title(f'M2 Wind Speed at 10m - Month {month} , 2026')
#     plt.xlabel('Wind Speed [m/s]')
#     plt.ylabel('Frequency')
#     plt.legend()
#     plt.show()

################################################################
#Wind rose plots for 50m and 80m 
#on a month to month basis (Feb-Oct 2026)
#Note: Keep the scale and probability bins consistent across months for comparison

# Wind rose for 50m month to month
SPEED_BINS = np.arange(0, 22, 2)  # fixed speed bins (m/s) shared by all months
RMAX = 20                         # fixed max radial frequency (%) shared by all months; raise if bars clip
# for month in range(2, 11):
#     mask = (time.dt.month == month) &     wind_dir50_clean.notna() & wind_speed50.notna()    
#     plt.figure(figsize=(8, 8))
#     ax = WindroseAxes.from_ax()
#     ax.bar(wind_dir50_clean[mask], wind_speed50[mask], normed=True, opening=0.8, edgecolor='white', bins=SPEED_BINS)
#     ax.set_ylim(0, RMAX)
#     ax.set_rgrids(np.linspace(0, RMAX, 5)[1:], labels=[f'{r:.0f}%' for r in np.linspace(0, RMAX, 5)[1:]])
#     ax.set_legend(title='Wind Speed [m/s]')
#     ax.set_title(f' M2 Wind Rose at 50m - Month {month}')
#     plt.show()
################################
#Wind rose for 80m month to month
# for month in range(2, 11):
#     mask = (time.dt.month == month) & wind_dir80_clean.notna() & wind_speed80_clean.notna()
#     plt.figure(figsize=(8, 8))
#     ax = WindroseAxes.from_ax()
#     ax.bar(wind_dir80_clean[mask], wind_speed80_clean[mask], normed=True, opening=0.8, edgecolor='white', bins=SPEED_BINS)
#     ax.set_ylim(0, RMAX)
#     ax.set_rgrids(np.linspace(0, RMAX, 5)[1:], labels=[f'{r:.0f}%' for r in np.linspace(0, RMAX, 5)[1:]])
#     ax.set_legend(title='Wind Speed [m/s]')
#     ax.set_title(f' M2 Wind Rose at 80m - Month {month}')
#     plt.show()

#######################################
# Finding Relevent Events from finding extreme events
