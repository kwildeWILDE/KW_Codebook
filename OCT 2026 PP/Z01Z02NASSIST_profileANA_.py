#import necessary libraries
from webbrowser import get

import pandas as pd
import numpy as np
import xarray as xr 
import matplotlib.pyplot as plt
import scipy.stats as stats
import os
import glob
import re

############################################################################ 
# importhing the data files from the Z01 Z02, and assist for the time ranfe of Feb to Oct 2026# 

### IMPORTING THE Z01 DATA FILES ### 

dp_z01 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data/corsair"
dfp_z01 = f"{dp_z01}//s40.lidar.z01.c1/order_bcf33e155d61445faecd3ae80"

#collect every NetCDF file in the directory, in order
nc_files_z01 = sorted(glob.glob(f"{dfp_z01}/*.nc"))
if not nc_files_z01:
    raise FileNotFoundError(f"No NetCDF files found in directory: {dfp_z01}")

#some files contain NaT times, which breaks by_coords' monotonic check,
#so concatenate along time, drop NaT/duplicate times, then sort.
ds_z01 = xr.open_mfdataset(nc_files_z01, combine='nested', concat_dim='time',
                           data_vars='minimal', coords='minimal', compat='override')
ds_z01 = ds_z01.isel(time=ds_z01['time'].notnull().values).sortby('time')
ds_z01 = ds_z01.isel(time=~ds_z01.get_index('time').duplicated())

print("Successfully loaded S40 LIDAR Z01 C1 data.")
print(ds_z01.head())
print('##' * 40)
z01_time = ds_z01['time']
print(z01_time)
ds_z01['datetime'] = ('time', pd.to_datetime(ds_z01['time'].astype(str).values))
print(ds_z01['datetime'])
print('##' * 40)

### IMPORTING THE Z02 DATA FILES ### 

dp_z02 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data/corsair"
dfp_z02 = f"{dp_z02}//s40.lidar.z02.c0/order_c49108bd613c4728aa7bdb10e"

#collect every NetCDF file in the directory, in order
nc_files_z02 = sorted(glob.glob(f"{dfp_z02}/*.nc"))
if not nc_files_z02:
    raise FileNotFoundError(f"No NetCDF files found in directory: {dfp_z02}")

#each file has a time cordinate, so combine them directly along it.
ds_z02 = xr.open_mfdataset(nc_files_z02, combine='nested', concat_dim='time',
                           data_vars='minimal', coords='minimal', compat='override')
ds_z02 = ds_z02.isel(time=ds_z02['time'].notnull().values).sortby('time')
ds_z02 = ds_z02.isel(time=~ds_z02.get_index('time').duplicated())

print("Successfully loaded S40 LIDAR Z02 C0 data.")
print(ds_z02.head(10))
print('##' * 40)

### IMPORTING THE ASSIST DATA FILES ### 
dp_at = "c:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.assist.tropoe.z01.c0"
at_files = f'{dp_at}/order_0345338a149b488b8aabb6f46'

#collect every .nc file in order of time 
nc_files = sorted(glob.glob(f'{at_files}/*.nc'))
if not nc_files:
    raise FileNotFoundError(f"No .nc files found in {at_files}")

#creatre the .nc files into a workable xarray dataset
# Each file already has a 'time' coordinate, so combine them directly along it.
ds_at = xr.open_mfdataset(nc_files, combine="by_coords", data_vars="minimal", coords="minimal", compat="override").sortby("time")

#check if the dataset has been loaded correctly
#print(ds_at.head())

#filter through the ASSIST dataset to keep only quality data
# From the WDH notes: 
## "Data with rmsa > 5 and gamma > 3 should be rejected. Data above cloud base height 
# #if the liquid water path is greater than 5 g/m^2 are also suspect."

#drop=True isn't supported on dask arrays, so bad data is masked as NaN instead
#variable names are cbh and lwp; cbh and height are both in km
ds_at_filtered = ds_at.where((ds_at['rmsa'] <= 5) & (ds_at['gamma'] <= 3))
ds_at_filtered = ds_at_filtered.where((ds_at_filtered['cbh'] <= ds_at_filtered['height']) | (ds_at_filtered['lwp'] <= 5))
print("ASSIST dataset successfully filtered")
print(ds_at_filtered.head())
print('##' * 40)

############################################################
# since the dataset loaded in well now it's time to algin them time wise 
ds_z02['datetime'] = ('time', pd.to_datetime(ds_z02['time'].astype(str).values))
ds_at_filtered['datetime'] = ('time', pd.to_datetime(ds_at_filtered['time'].astype(str).values))
ds_z01 = ds_z01.set_index(time='datetime')
ds_z02 = ds_z02.set_index(time='datetime')
ds_at_filtered = ds_at_filtered.set_index(time='datetime')

print("Datasets successfully aligned by datetime index.")
print('##' * 40)
print("Z01 dataset head:")
print(ds_z01.head())
print('##' * 40)
print("Z02 dataset head:")
print(ds_z02.head())
print('##' * 40)
print("ASSIST filtered dataset head:")
print(ds_at_filtered.head())
print('##' * 40)

## Create a plot of the timeline for the plots to double check alignment
# where the x-axis is the overall time from Feb to October and then y is the repective datasets with horizonatal lines representing how far the 
# dataset time coverage

import matplotlib.pyplot as plt

def time_range(ds):
    # works whether or not the time index was replaced by 'datetime'
    t = pd.to_datetime(ds['time'].astype(str).values)
    t = t[~t.isna()]
    return t.min(), t.max()

spans = {
    'Z01': time_range(ds_z01),
    'Z02': time_range(ds_z02),
    'ASSIST': time_range(ds_at_filtered),
}

# fig, ax = plt.subplots(figsize=(15, 4))
# for y, (name, (start, end)) in enumerate(spans.items(), start=1):
#     ax.hlines(y, start, end, linewidth=6, label=f'{name}: {start:%Y-%m-%d} to {end:%Y-%m-%d}')
# ax.set_yticks(range(1, len(spans) + 1))
# ax.set_yticklabels(spans.keys())
# ax.set_ylim(0.5, len(spans) + 0.5)
# ax.set_xlim(pd.Timestamp('2026-02-01'), pd.Timestamp('2026-10-31'))
# ax.set_xlabel('Datetime')
# ax.set_title('Time coverage of Z01, Z02, and ASSIST Datasets')
# ax.grid(axis='x', alpha=0.3)
# ax.legend(loc='upper right')
# plt.tight_layout()
# plt.show()

#################################################################### 
# Now that we can see the periods where there is a time agreement between the datasets, we can proceed with further analysis.
# Now we can work on crating shared temperature (from the assist) and the wind profiles (from z01 and z02) during an exact time

# First group of extreme event times 
## APRIL 23 06:00 UTC
## APRIL 23 13:00 UTC
## APRIL 23 14:00 UTC
## APRIL 23 15:00 UTC
## APRIL 23 16:00 UTC

#SECOND group of extreme event times 
## MAY 7 07:00 UTC
## MAY 7 08:00 UTC
## MAY 7 12:00 UTC
## MAY 7 14:00 UTC



# Build the profile plots: one figure per event group, one subplot per time.
# Temperature (ASSIST) on the bottom axis, wind speed (Z01 and Z02) on the top axis.
MAX_ALT = 1000          # m
TOL = pd.Timedelta('30min')   # max gap allowed between requested and nearest sample

event_groups = {
    'April 23, 2026': [f'2026-04-23 {h}:00' for h in ('06', '13', '14', '15', '16')],
    'May 7, 2026':    [f'2026-05-07 {h}:00' for h in ('07', '08', '12', '14')],
}

def nearest_profile(ds, target):
    t = pd.to_datetime(ds['time'].values)
    i = np.abs(t - target).argmin()
    if abs(t[i] - target) > TOL:
        return None, None
    return ds.isel(time=i), t[i]

def plot_event_group(title, times):
    n = len(times)
    ncols = min(n, 3)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 7.5 * nrows), squeeze=False)
    temp_color, z01_color, z02_color = '#E06000', '#7B6FBF', '#2E8B57'

    for ax, ts in zip(axes.flat, times):
        target = pd.Timestamp(ts)
        at, at_t = nearest_profile(ds_at_filtered, target)
        w1, w1_t = nearest_profile(ds_z01, target)
        w2, w2_t = nearest_profile(ds_z02, target)

        ax.set_ylim(0, MAX_ALT)
        ax.set_ylabel('Altitude (m)')
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.set_title(f'{target:%H:%M} UTC', pad=45)

        if at is not None:
            h = at['height'].values * 1000   # km -> m
            ax.plot(at['temperature'].values, h, color=temp_color, lw=2.5, label='ASSIST temp')
        ax.set_xlabel('Temperature (C)', color=temp_color)
        ax.tick_params(axis='x', colors=temp_color)

        axw = ax.twiny()
        if w1 is not None:
            axw.plot(w1['WS'].values, w1['height'].values, '--', color=z01_color, lw=2.5, label='Z01 wind')
        if w2 is not None:
            axw.plot(w2['wind_speed'].values, w2['distance'].values, '--', color=z02_color, lw=2.5, label='Z02 wind')
        axw.set_xlabel('Wind Speed (m/s)', color=z01_color)
        axw.tick_params(axis='x', colors=z01_color)

        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = axw.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc='lower right', fontsize=8)

    for ax in list(axes.flat)[n:]:
        ax.set_visible(False)
    fig.suptitle(f'Temperature and Wind Profiles - {title}', fontsize=14)
    fig.tight_layout(h_pad=4, w_pad=3, rect=(0, 0, 1, 0.96))

for title, times in event_groups.items():
    plot_event_group(title, times)
plt.show()
##################################################

