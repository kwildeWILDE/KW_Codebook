#import necessary libraries
from webbrowser import get

import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import matplotlib.colors as mcolors
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
import re

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
################################################################
z01_h = ds_z01['height'] 

z01_ws = ds_z01['WS']

# Print each height and the number of valid wind-speed data points.
valid_ws_counts = z01_ws.count(dim='time')
height_ws_counts = pd.DataFrame({
    'height': z01_h.values,
    'valid_ws_count': valid_ws_counts.values
})
print(height_ws_counts.to_string(index=False))

#wind speed at 200 m (select by height value, not by index) 
z01_ws_200 = ds_z01['WS'].sel(height=200)

#create a month varible 
ds_z01['month'] = ds_z01['datetime'].dt.month
#create a month by month wind speed timeline plot at 200 m 
months = np.unique(ds_z01['month'].values)
# for month in months:
#     plt.figure(figsize=(12, 6))
#     in_month = (ds_z01['month'] == month).values
#     ws_month = z01_ws_200.isel(time=in_month)
#     time_month = ds_z01['datetime'].isel(time=in_month)
#     valid = (ws_month > 0).values
#     plt.plot(time_month.values[valid], ws_month.values[valid],
#              label='120m', color='orange', alpha=0.8)
#     plt.xlabel('UTC Time')
#     plt.ylabel('Wind Speed (m/s)')
#     plt.title(f'Z01 Wind Speed at 120 m (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

############################################################################
#make a frequency hitogram with a weibull fit for windspeed at 200 m 
#on a month by month basis

# for month in months:
#     plt.figure(figsize=(12, 6))
#     in_month = (ds_z01['month'] == month).values
#     ws_month = z01_ws_200.isel(time=in_month)
#     valid = (ws_month > 0).values
#     ws_valid = ws_month.values[valid]
#     plt.hist(ws_valid, bins=20, density=True, alpha=0.6, color='orange', label='200m')
#     if len(ws_valid) > 0:
#         shape, loc, scale = weibull_min.fit(ws_valid, floc=0)
#         x = np.linspace(0, ws_valid.max(), 100)
#         plt.plot(x, weibull_min.pdf(x, shape, loc, scale), 'r-', lw=2, label='Weibull fit')
#     plt.xlabel('Wind Speed (m/s)')
#     plt.ylabel('Frequency')
#     plt.title(f'Z01 Wind Speed Frequency at 200 m (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

####################################################################
#Make a wind rose plot for wind speed at 200 m on a month by month basis

# for month in months:
#     plt.figure(figsize=(10, 8))
#     in_month = (ds_z01['month'] == month).values
#     ws_month = z01_ws_200.isel(time=in_month)
#     wd_month = ds_z01['WD'].sel(height=200).isel(time=in_month)
#     valid = ((ws_month > 0) & wd_month.notnull()).values
#     ws_valid = ws_month.values[valid]
#     wd_valid = wd_month.values[valid]
#     if len(ws_valid) > 0:
#         ax = WindroseAxes.from_ax()
#         speed_bins = np.arange(0, ws_valid.max() + 1, 1)
#         cmap = plt.get_cmap('viridis')
#         ax.bar(wd_valid, ws_valid, normed=True, opening=0.8, edgecolor='white', cmap=cmap, bins=speed_bins)
#         ax.set_legend(loc='lower right')
#         plt.title(f'Z01 Wind Rose at 200 m (Month: {month}, 2026)')
#         plt.tight_layout()
#         plt.show()
##########################################################################################
#Do the same timeline, histogram, and wind rose analysis for wind speed at 200 m
#wind speed at 500 m (select by height value, not by index)
z01_ws_500 = ds_z01['WS'].sel(height=500)
    
#timeline plot for wind speed at 500 m on a month by month basis
# for month in months:
#     plt.figure(figsize=(12, 6))
#     in_month = (ds_z01['month'] == month).values
#     ws_month = z01_ws_500.isel(time=in_month)
#     time_month = ds_z01['datetime'].isel(time=in_month)
#     valid = (ws_month > 0).values
#     plt.plot(time_month.values[valid], ws_month.values[valid],
#              label='500m', color='purple', alpha=0.8)
#     plt.xlabel('UTC Time')
#     plt.ylabel('Wind Speed (m/s)')
#     plt.title(f'Z01 Wind Speed at 500 m (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

# #histogram plot for wind speed at 500 m on a month by month basis
for month in months:
    plt.figure(figsize=(10, 6))
    in_month = (ds_z01['month'] == month).values
    ws_month = z01_ws_500.isel(time=in_month)
    valid = (ws_month > 0).values
    ws_valid = ws_month.values[valid]
    plt.hist(ws_valid, bins=20, density=True, alpha=0.6, color='purple', label='500m')
    if len(ws_valid) > 0:
        shape, loc, scale = weibull_min.fit(ws_valid, floc=0)
        x = np.linspace(0, ws_valid.max(), 100)
        plt.plot(x, weibull_min.pdf(x, shape, loc, scale), 'r-', lw=2, label='Weibull fit')
    plt.xlabel('Wind Speed (m/s)')
    plt.ylabel('Frequency')
    plt.title(f'Z01 Wind Speed Frequency at 500 m (Month: {month}, 2026)')
    plt.legend()
    plt.tight_layout()
    plt.grid(True, alpha=0.2, ls='--')
    plt.show()

# #wind rose plot for wind speed at 500 m on a month by month basis
# for month in months:
#     plt.figure(figsize=(10, 8))
#     in_month = (ds_z01['month'] == month).values
#     ws_month = z01_ws_500.isel(time=in_month)
#     wd_month = ds_z01['WD'].sel(height=500).isel(time=in_month)
#     valid = ((ws_month > 0) & wd_month.notnull()).values
#     ws_valid = ws_month.values[valid]
#     wd_valid = wd_month.values[valid]
#     if len(ws_valid) > 0:
#         ax = WindroseAxes.from_ax()
#         speed_bins = np.arange(0, ws_valid.max() + 1, 1)
#         cmap = plt.get_cmap('viridis')
#         ax.bar(wd_valid, ws_valid, normed=True, opening=0.8, edgecolor='white', cmap=cmap, bins=speed_bins)
#         ax.set_legend(loc='lower right')
#         plt.title(f'Z01 Wind Rose at 500 m (Month: {month}, 2026)')
#         plt.tight_layout()
#         plt.show()