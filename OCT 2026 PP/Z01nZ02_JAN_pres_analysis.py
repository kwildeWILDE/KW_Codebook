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
#keep only what the plot needs (WS, heights <= 500 m) and load it into memory once
ds_z01 = ds_z01[['WS']].sel(height=slice(0, 500))
ds_z01 = ds_z01.isel(time=ds_z01['time'].notnull().values).sortby('time')
ds_z01 = ds_z01.isel(time=~ds_z01.get_index('time').duplicated()).load()

print("Successfully loaded S40 LIDAR Z01 C1 data.")

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
ds_z02 = ds_z02[['wind_speed']]
ds_z02 = ds_z02.isel(time=ds_z02['time'].notnull().values).sortby('time')
ds_z02 = ds_z02.isel(time=~ds_z02.get_index('time').duplicated()).load()

print("Successfully loaded S40 LIDAR Z02 C0 data.")

#Z01 time stamps are irregular (~30 min scans, e.g. 21:39:46) while Z02 is on an exact
#10-min grid, so an exact-match intersection is empty. Average both onto a common 30-min grid.
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
#combine Z01 and Z02 at every time step first (average where both exist, otherwise whichever exists)
ds_merged['WS_comb'] = xr.concat([ds_merged['WS_z01'], ds_merged['WS_z02']],
                                 dim='src').mean('src', skipna=True)
#then, for each month and hour of day, average over all days of that month at that hour (per height)
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
#combined profile WS_comb is computed per time step above
ws_var = 'WS_comb'
max_height = 500   #m AGL upper limit of the plots
months = [m for m in range(3, 13) if m in mean_wind_profiles['month'].values]
min_count = 10   #points with fewer than this many valid samples in the month/hour average are left blank
counts = ds_merged['WS_comb'].groupby(['month', 'hour']).count(dim='time')
ws_masked = mean_wind_profiles[ws_var].where(counts >= min_count)
#tight color scale from the data that remains
#vmin = float(np.floor(ws_masked.min()))
vmin = 3 # set minimum wind speed for color scale
# vmax = float(np.ceil(ws_masked.max()))
vmax = 10 # set maximum wind speed for color scale
levels = np.linspace(vmin, vmax, 15)   #contourf ignores vmin/vmax unless levels are given

#only plot months that have data
# ncols = min(6, len(months))
# nrows = int(np.ceil(len(months) / ncols))
# fig, axes = plt.subplots(nrows, ncols, figsize=(3 * ncols, 3.5 * nrows),
#                          sharex=True, sharey=True, squeeze=False, layout='constrained')
# for ax in axes.flat[len(months):]:
#     ax.set_visible(False)
# for ax, month in zip(axes.flat, months):
#     ax.set_title(pd.Timestamp(2026, month, 1).strftime('%B'), fontsize=9, loc='left')
#     prof = ws_masked.sel(month=month).transpose('height', 'hour')
#     prof = prof.sel(height=slice(0, max_height))
#     hrs, hts = prof['hour'].values, prof['height'].values
#     # use contourf + contour to make it less pixelated
#     pcm = ax.contourf(hrs, hts, prof.values, levels=levels, cmap='viridis', extend='both')
#     ax.contour(hrs, hts, prof.values, levels=levels, colors='k', linewidths=0.5, alpha=0.5)
#     ax.set_xticks([0, 6, 12, 18])
#     ax.set_ylim(0, max_height)
# for ax in axes[-1]:
#     ax.set_xlabel('Time (UTC)')
# for ax in axes[:, 0]:
#     ax.set_ylabel('Height (m AGL)')
# #colorbar and legend sit below the panels so they don't crowd the plots
# fig.colorbar(pcm, ax=axes, location='bottom', shrink=0.5, aspect=40, pad=0.03,
#              label='Mean wind speed (m/s)')
# fig.suptitle('Monthly Diurnal Cycle of Mean Wind Speed from Combined lidar Z01 and Z02', fontsize=10)
# plt.show()

###################################################################################
# Make a linear regression plot from the wind speeds from z01 and z02 at the same heights and times
# to see if there is agreement between the two lidars
z01_var = 'WS_z01'
z02_var = 'WS_z02'

# select only the times and heights where both lidars have data
common_mask = ds_merged[z01_var].notnull() & ds_merged[z02_var].notnull()
ws_z01_common = ds_merged[z01_var].where(common_mask)
ws_z02_common = ds_merged[z02_var].where(common_mask)

# flatten the data for regression plotting
ws_z01_flat = ws_z01_common.values.flatten()
ws_z02_flat = ws_z02_common.values.flatten()

# remove NaNs from the flattened arrays
valid_mask = ~np.isnan(ws_z01_flat) & ~np.isnan(ws_z02_flat)
ws_z01_flat = ws_z01_flat[valid_mask]
ws_z02_flat = ws_z02_flat[valid_mask]

# create the linear regression plot
plt.figure(figsize=(6, 6))
plt.scatter(ws_z01_flat, ws_z02_flat, alpha=0.5)
plt.xlabel('Z01 Wind Speed (m/s)')
plt.ylabel('Z02 Wind Speed (m/s)')
plt.title('Linear Regression of Wind Speeds from Z01 and Z02')
# fit a linear regression line
# calculate the slope and intercept for the linear regression line
# calculate the slope and intercept for the linear regression line using numpy's polyfit function
m, b = np.polyfit(ws_z01_flat, ws_z02_flat, 1)
plt.plot(ws_z01_flat, m * ws_z01_flat + b, color='red', label='Linear Fit (y = {:.2f}x + {:.2f})'.format(m, b))
plt.legend(loc='best')
plt.show()