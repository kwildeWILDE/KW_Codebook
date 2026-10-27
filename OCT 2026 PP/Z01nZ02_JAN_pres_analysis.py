#import necessary libraries
from webbrowser import get

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
import re

#pull the datasets
##PULLING THE DATA FROM THE S40.LIDAR.Z01.C1 FROM WDH #######
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

##############################################
###PULLING THE DATA FROM THE S40.LIDAR.Z02.C0 FROM WDH ################

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

#######################################################
#make sure the time coordinates between Z01 and Z02 datasets are aligned
z02_time = ds_z02['time']
print(z02_time)
ds_z02['time'] = ('time', pd.to_datetime(ds_z02['time'].astype(str).values))
print(ds_z02['time'])

#Z01 time stamps are irregular (~30 min scans, e.g. 21:39:46) while Z02 is on an exact
#10-min grid, so an exact-match intersection is empty. Average both onto a common 30-min grid.
ds_z01 = ds_z01.drop_vars('datetime', errors='ignore')
z01_30 = ds_z01.resample(time='30min').mean()

#Z02: only keep the wind speed profile, use the same dimension/variable naming as Z01
z02_ws = ds_z02[['wind_speed']].rename({'distance': 'height', 'wind_speed': 'WS_z02'})
z02_30 = z02_ws.resample(time='30min').mean()
z01_30 = z01_30.rename({'WS': 'WS_z01'})

print("Z01 30-min grid:", z01_30.sizes)
print("Z02 30-min grid:", z02_30.sizes)

#####################################
## if the time coordinates were not aligned initially, we have now aligned them to common times.
# we can merge the Z01 and Z02 datasets along the time dimension
#keep only times present in both datasets; heights are outer-joined so Z01 keeps its full
#0-3000 m range (Z02 only covers 40-300 m and is NaN above that)
common_times = np.intersect1d(z01_30['time'].values, z02_30['time'].values)
ds_merged = xr.merge([z01_30[['WS_z01']].sel(time=common_times),
                      z02_30.sel(time=common_times)], join='outer')
print("Merged dataset:")
print(ds_merged)

#########################
# WITH THE merged dataset, start to make a mean wind speed profiles for the diurnal cycle on a month to month basis
# group the merged dataset by month and hour to calculate the mean wind speed profiles
ds_merged = ds_merged.assign_coords(month=('time', ds_merged['time'].dt.month.values),
                                    hour=('time', ds_merged['time'].dt.hour.values))
mean_wind_profiles = (ds_merged.groupby(['month', 'hour']).mean(dim='time'))
print("Mean wind speed profiles (month x hour x height):")
print(mean_wind_profiles)

#overall mean profile per height, and a quick comparison plot
overall = ds_merged[['WS_z01', 'WS_z02']].mean(dim='time')
# fig, ax = plt.subplots()
# ax.plot(overall['WS_z01'], overall['height'], label='Z01')
# ax.plot(overall['WS_z02'], overall['height'], label='Z02')
# ax.set_xlabel('Mean wind speed (m/s)')
# ax.set_ylabel('Height AGL (m)')
# ax.legend()
# plt.show()



#########################
# MONTHLY DIURNAL CYCLE PANELS: color = mean wind speed (hour x height)
#combined profile: average of Z01 and Z02 where both exist (40-300 m), Z01 only elsewhere
mean_wind_profiles['WS_comb'] = xr.concat([mean_wind_profiles['WS_z01'], mean_wind_profiles['WS_z02']],
                                          dim='src').mean('src', skipna=True)
ws_var = 'WS_comb'
max_height = 500   #m AGL upper limit of the plots
months = [m for m in range(1, 13) if m in mean_wind_profiles['month'].values]
vmin = float(mean_wind_profiles[ws_var].min())
vmax = float(mean_wind_profiles[ws_var].max())

#only plot months that have data
ncols = min(6, len(months))
nrows = int(np.ceil(len(months) / ncols))
fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols, 3.5 * nrows),
                         sharex=True, sharey=True, squeeze=False, layout='constrained')
for ax in axes.flat[len(months):]:
    ax.set_visible(False)
for ax, month in zip(axes.flat, months):
    ax.set_title(pd.Timestamp(2026, month, 1).strftime('%B'), fontsize=9, loc='left')
    prof = mean_wind_profiles[ws_var].sel(month=month).transpose('height', 'hour')
    prof = prof.sel(height=slice(0, max_height))
    hrs, hts = prof['hour'].values, prof['height'].values
    pcm = ax.pcolormesh(hrs, hts, prof.values, cmap='viridis', vmin=vmin, vmax=vmax, shading='nearest')
    ax.set_xticks([0, 6, 12, 18])
    ax.set_ylim(0, max_height)
for ax in axes[-1]:
    ax.set_xlabel('Time (UTC)')
for ax in axes[:, 0]:
    ax.set_ylabel('Height (m AGL)')
#colorbar and legend sit below the panels so they don't crowd the plots
fig.colorbar(pcm, ax=axes, location='bottom', shrink=0.5, aspect=40, pad=0.03,
             label='Mean wind speed (m/s)')
fig.suptitle('Monthly Diurnal Cycle of Mean Wind Speed from combined lidar Z01 and Z02', fontsize=10)
plt.show()