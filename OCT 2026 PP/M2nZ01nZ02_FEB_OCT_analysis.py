#import necessary libraries
from webbrowser import get

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import xarray as xr
import glob
import os
import re
import scipy.stats as stats
from scipy.stats import weibull_min, norm, gaussian_kde
from scipy.stats import linregress

#######################################################################
# Importing the M2 dataset #

dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_FULL_JAN31_OCT31_2026_Datapull.xlsx"

#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)

print(ds_m2.head())

#from looking over the plot and the excel data there are varibles that have been recorded as "-99999"
#replace these with NaN for proper analysis
ds_m2 = ds_m2.replace(-99999, np.nan)

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

# Include including the filter to remove "flat values"
MIN_FLAT_RUN = 6  # consecutive identical samples treated as flat; adjust to the M2 sampling interval

def mask_flat_runs(series, min_run=MIN_FLAT_RUN):
    run_id = (series != series.shift()).cumsum()
    run_len = series.groupby(run_id).transform('size')
    return series.mask((run_len >= min_run) & series.notna())

#######################################################################
#pulling the z02 dataset #

# Pulling the wind data from the WDH s40.lidars
#s40.lidar.z02.c0
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

################################################################
# Pulling the Z01 dataset #
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

#################################################################
# When it comes to the M2 dataset, "re-sample" it as so that it has the same time interval as the Z01 and Z02 datasets (10 minutes)
# Within the Z01 and Z02 datasets, ensure that the time intervals are consistent and any flat runs are masked.
#for example, for the data with the timestamp as of 00:05 is the average of the data from 00:00 to 00:10. 
# This can be achieved using the resample method in xarray, specifying the time interval and the aggregation function (mean).

#double check that the resampling aligns with the desired 10-minute intervals for Z01 and Z02 datasets.
#Check the sampling interval of each lidar dataset ('T' was removed in pandas; use 'min')
t_z01 = ds_z01.get_index('time')
t_z02 = ds_z02.get_index('time')
print("Z01 interval counts:\n", pd.Series(t_z01).diff().value_counts().head())
print("Z02 interval counts:\n", pd.Series(t_z02).diff().value_counts().head())

#Check that Z01 and Z02 timestamps line up
common = t_z01.intersection(t_z02)
print(f"Z01: {len(t_z01)}, Z02: {len(t_z02)}, common timestamps: {len(common)}")
print("Only in Z01:", len(t_z01.difference(t_z02)), "| Only in Z02:", len(t_z02.difference(t_z01)))

#Resample M2 (UTC) to 10 minutes, same convention as the lidars (adjust label/closed if needed)
m2_10min = (ds_m2.set_index('UTC_time')
                 .select_dtypes(include='number')
                 .resample('10min', label='right', closed='right').mean())
# print(m2_10min.head())

#####################################################################################################
#create a frequency histogram with a weibull fit line for wind speed for
## 10m wind speed from the M2 dataset (blue histogram, with red Weibull fit line)
##50 m wind speed from the M2 and the Z02 dataset (green M2 histogram w/ alpha=0.6, blue Z02 histogram w/ alpha=0.6, with red Weibull fit line, ls "-", for the weibul fit from the M2 data, ls "--" for the weibull foit from the Z02 data)
## 80 m wind speed from the M2 and the Z02 dataset (red M2 histogram w/ alpha=0.6, purple Z02 histogram w/ alpha=0.6, with red Weibull fit line, ls "-", for the weibul fit from the M2 data, ls "--" for the weibull foit from the Z02 data)
## 200 m wind speed from the Z01 dataset (organge histogram, with red Weibull fit line, ls "-", for the weibull fit from the Z01 data)
## 500 m wind speed from the Z01 dataset (purple histogram, with red Weibull fit line, ls "-", for the weibull fit from the Z01 data)

desired_heights = [10, 50, 80, 200, 500]  # metres

def m2_ws(h):
    return m2_10min[f'Avg Wind Speed @ {h}m [m/s]'].to_numpy()

# Z01 heights are named 'height'; Z02 heights are named 'distance' and start at 40 m
# with 20 m spacing, so 50 m is linearly interpolated between 40 m and 60 m.
def z01_ws(h):
    return ds_z01['WS'].sel(height=h).to_numpy()

def z02_ws(h):
    da = ds_z02['wind_speed']
    if h in da['distance'].values:
        return da.sel(distance=h).to_numpy()
    return da.interp(distance=h).to_numpy()

# (height, [(label, data, histogram colour, linestyle for Weibull fit)])
panels = [
    (10,  [('M2', m2_ws(10), 'blue', '-')]),
    (50,  [('M2', m2_ws(50), 'green', '-'), ('Z02', z02_ws(50), 'blue', '--')]),
    (80,  [('M2', m2_ws(80), 'red', '-'), ('Z02', z02_ws(80), 'purple', '--')]),
    (200, [('Z01', z01_ws(200), 'orange', '-')]),
    (500, [('Z01', z01_ws(500), 'purple', '-')]),
]

# def plot_weibull_histogram(data, ax, bins=30, color='blue', label=None, ls='-'):
#     data = data[np.isfinite(data)]
#     data = data[data > 0]  # Weibull with floc=0 needs positive values
#     shape, loc, scale = weibull_min.fit(data, floc=0)
#     ax.hist(data, bins=bins, density=True, alpha=0.6, color=color, label=f'{label} data')
#     x = np.linspace(0, data.max(), 200)
#     ax.plot(x, weibull_min.pdf(x, shape, loc, scale), color='red', ls=ls, lw=2,
#             label=f'{label} Weibull (k={shape:.2f}, c={scale:.2f})')

# # Feb - Oct 2026, one subplot per height
# fig, axes = plt.subplots(3, 2, figsize=(12, 11), sharex=True, sharey=True,
#                          constrained_layout=True)
# axes = axes.ravel()
# for ax, (h, series) in zip(axes, panels):
#     for label, data, color, ls in series:
#         plot_weibull_histogram(data, ax, color=color, label=label, ls=ls)
#     ax.set_title(f'{h} m', fontsize=11, loc='left')
#     ax.legend(fontsize=7, loc='upper right', frameon=False)
#     ax.xaxis.set_major_locator(plt.MultipleLocator(2))
#     ax.tick_params(labelbottom=True)
# for ax in axes[len(panels):]:
#     ax.set_visible(False)
# axes[-1].set_visible(False)
# fig.supxlabel('Wind speed (m/s)')
# fig.supylabel('Frequency density')
# fig.suptitle('Wind speed distributions, Feb - Oct 2026')
# for ax in axes:
#     ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
# plt.tight_layout()
# plt.show()
################################################################################## 

#with the M2 and the z02 datasets, in the same 10 minitue intervals create a linear regression of the wind speed data 
# at the heights of 50 m and 80 m (in their own subplots)
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharex=True, sharey=True,
                         constrained_layout=True)
axes = axes.ravel()
heights = [50, 80]
for ax, h in zip(axes, heights):
    # Align on timestamps (the two series have different lengths/time axes)
    m2_series = m2_10min[f'Avg Wind Speed @ {h}m [m/s]']
    da = ds_z02['wind_speed']
    da = da.sel(distance=h) if h in da['distance'].values else da.interp(distance=h)
    z02_series = pd.Series(da.to_numpy(), index=t_z02)
    paired = pd.concat([m2_series.rename('m2'), z02_series.rename('z02')],
                       axis=1, join='inner').replace([np.inf, -np.inf], np.nan).dropna()
    print(f"{h} m: {len(paired)} matched 10-min points")
    m2_data = paired['m2'].to_numpy()
    z02_data = paired['z02'].to_numpy()
    slope, intercept, r_value, p_value, std_err = linregress(m2_data, z02_data)
    ax.scatter(m2_data, z02_data, alpha=0.6, label='Data')
    x = np.linspace(m2_data.min(), m2_data.max(), 100)
    ax.plot(x, intercept + slope * x, 'r-', label=f'Fit: y={slope:.2f}x+{intercept:.2f}\nR²={r_value**2:.2f}')
    ax.set_title(f'{h} m', fontsize=11, loc='left')
    ax.set_xlabel('M2 wind speed (m/s)')
    ax.set_ylabel('Z02 wind speed (m/s)')
    ax.legend(fontsize=7, loc='upper left', frameon=False)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
plt.tight_layout()
plt.show()