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
# Upload the APRIL ddoppler datasets 
dp_dp1 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data"
df_dp1 = f'{dp_dp1}/corsair/fc.ddoppler.z01.c1/order_c9d0c27eec5a4cb9a447c16e4'

#create one xarra dataset from all NetCDF files in order 
nc_files = glob.glob(f'{df_dp1}/*.nc')
if not nc_files:
    raise FileNotFoundError(f"No NetCDF files found in directory {df_dp1}")

#these files store timestamps in global attributes rather than coordinates 
datasets = []
for filepath in nc_files:
	file_ds = xr.open_dataset(filepath)
	start_time = file_ds.attrs.get("start_time")
	if start_time is None:
		file_ds.close()
		raise ValueError(f"Missing start_time attribute in {filepath}")
	datasets.append(file_ds.expand_dims(time=[pd.to_datetime(start_time)]))

ds_dp1 = xr.concat(datasets, dim="time").sortby("time")

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds_dp1.data_vars))
print("Dimensions:", dict(ds_dp1.sizes))
print("Max Wind Speed:", ds_dp1["WS"].max().values)
print("Min Wind Speed:", ds_dp1["WS"].min().values)  # Print wind speed values for verification

#getting the wind speed values and filtering out NaN values for analysis
ws_values = ds_dp1["WS"].values
valid_ws_values = ws_values[np.isfinite(ws_values)]
print("Non-NaN wind speed values:", valid_ws_values)
print("Max valid wind speed:", np.max(valid_ws_values))
print("Min valid wind speed:", np.min(valid_ws_values))

#In the mettadata sigma_WS is the standard deviation of the wind speed measurements,
## which can be used as a quality indicator. We will filter out any values that are NaN or exceed a reasonable threshold for sigma_WS.
sig_ws_values = ds_dp1["sigma_WS"].values
valid_sig_ws_values = sig_ws_values[np.isfinite(sig_ws_values)]
print("Non-NaN sigma wind speed values:", valid_sig_ws_values)


# Treat sigma_WS as a quality indicator, not as a correction to WS.
MAX_SIGMA_WS = 1.0
MAX_WIND_SPEED = np.mean(valid_ws_values) + 2 * np.std(valid_ws_values)  # Set a reasonable maximum wind speed for plotting
## ^^ The reason for using mean + 2*std is to capture the majority of the data while excluding extreme outliers (i.e. + 2 values outside the std)
##typically the 2+ std method captures about 95% of the data in a normal distribution
#  This threshold helps ensure that the plotted wind speeds are representative 
# of typical conditions rather than being dominated by rare, extreme events.
print("Maximum wind speed for plotting:", MAX_WIND_SPEED)

# Filter the wind speed values based on the quality indicator and maximum wind speed
# Mask on the full arrays so WS and sigma_WS stay aligned (NaN comparisons are False)
mask = (ds_dp1["sigma_WS"] <= MAX_SIGMA_WS) & (ds_dp1["WS"] <= MAX_WIND_SPEED)
ds_dp1["WS_filtered"] = ds_dp1["WS"].where(mask)
filtered_ws_values = ds_dp1["WS_filtered"].values
filtered_ws_values = filtered_ws_values[np.isfinite(filtered_ws_values)]
# print("Filtered wind speed values:", filtered_ws_values)
# print("Max filtered wind speed:", np.max(filtered_ws_values))
# print("Min filtered wind speed:", np.min(filtered_ws_values))

#########################################################
# Summary of filtered wind speed values
print("Number of valid wind speed values:", len(valid_ws_values))
print("Number of filtered wind speed values:", len(filtered_ws_values))
print("Percentage of data retained after filtering:", 100 * len(filtered_ws_values) / len(valid_ws_values))
##########################################################
##
#Upload the MAY ddoppler dataset
dp_dp2 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data"
df_dp2 = f'{dp_dp2}/corsair/fc.ddoppler.z01.c1/order_801ccf2d61234e8982974a026'

#create one xarra dataset from all NetCDF files in order 
nc_files = glob.glob(f'{df_dp2}/*.nc')
if not nc_files:
    raise FileNotFoundError(f"No NetCDF files found in directory {df_dp2}")

#these files store timestamps in global attributes rather than coordinates 
datasets = []
for filepath in nc_files:
	file_ds = xr.open_dataset(filepath)
	start_time = file_ds.attrs.get("start_time")
	if start_time is None:
		file_ds.close()
		raise ValueError(f"Missing start_time attribute in {filepath}")
	datasets.append(file_ds.expand_dims(time=[pd.to_datetime(start_time)]))

ds_dp2 = xr.concat(datasets, dim="time").sortby("time")

#In the mettadata sigma_WS is the standard deviation of the wind speed measurements,
## which can be used as a quality indicator. We will filter out any values that are NaN or exceed a reasonable threshold for sigma_WS.
sig_ws_values = ds_dp2["sigma_WS"].values
valid_sig_ws_values = sig_ws_values[np.isfinite(sig_ws_values)]
print("Non-NaN sigma wind speed values:", valid_sig_ws_values)


# Treat sigma_WS as a quality indicator, not as a correction to WS.
MAX_SIGMA_WS = 1.0
may_ws_values = ds_dp2["WS"].values
valid_may_ws_values = may_ws_values[np.isfinite(may_ws_values)]
if not valid_may_ws_values.size:
    raise ValueError("No valid wind speed values found in the May Doppler dataset.")
MAX_WIND_SPEED = np.mean(valid_may_ws_values) + 2 * np.std(valid_may_ws_values)  # Set a reasonable maximum wind speed for plotting
## ^^ The reason for using mean + 2*std is to capture the majority of the data while excluding extreme outliers (i.e. + 2 values outside the std)
##typically the 2+ std method captures about 95% of the data in a normal distribution
#  This threshold helps ensure that the plotted wind speeds are representative 
# of typical conditions rather than being dominated by rare, extreme events.
print("Maximum wind speed for plotting:", MAX_WIND_SPEED)

# Filter the wind speed values based on the quality indicator and maximum wind speed
# Mask on the full arrays so WS and sigma_WS stay aligned (NaN comparisons are False)
mask = (ds_dp2["sigma_WS"] <= MAX_SIGMA_WS) & (ds_dp2["WS"] <= MAX_WIND_SPEED)
ds_dp2["WS_filtered"] = ds_dp2["WS"].where(mask)
filtered_ws_values = ds_dp2["WS_filtered"].values
filtered_ws_values = filtered_ws_values[np.isfinite(filtered_ws_values)]
print("Filtered wind speed values:", filtered_ws_values)
###########################################################################
# Align datasets by datetime index for further analysis
#######################################################################
# since the dataset loaded in well now it's time to algin them time wise 
ds_z02['datetime'] = ('time', pd.to_datetime(ds_z02['time'].astype(str).values))
ds_at_filtered['datetime'] = ('time', pd.to_datetime(ds_at_filtered['time'].astype(str).values))
ds_dp1['datetime'] = ('time', pd.to_datetime(ds_dp1['time'].astype(str).values))
ds_dp2['datetime'] = ('time', pd.to_datetime(ds_dp2['time'].astype(str).values))
ds_z01 = ds_z01.set_index(time='datetime')
ds_z02 = ds_z02.set_index(time='datetime')
ds_at_filtered = ds_at_filtered.set_index(time='datetime')
ds_dp1 = ds_dp1.set_index(time='datetime')
ds_dp2 = ds_dp2.set_index(time='datetime')

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
print("April Doppler dataset head:")
print(ds_dp1.head())
print('##' * 40)
print("May Doppler dataset head:")
print(ds_dp2.head())
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
    'April Doppler': time_range(ds_dp1),
    'May Doppler': time_range(ds_dp2),
}

# fig, ax = plt.subplots(figsize=(15, 4))
# for y, (name, (start, end)) in enumerate(spans.items(), start=1):
#     ax.hlines(y, start, end, linewidth=6, label=f'{name}: {start:%Y-%m-%d} to {end:%Y-%m-%d}')
# ax.set_yticks(range(1, len(spans) + 1))
# ax.set_yticklabels(spans.keys())
# ax.set_ylim(0.5, len(spans) + 0.5)
# ax.set_xlim(pd.Timestamp('2026-02-01'), pd.Timestamp('2026-10-31'))
# ax.set_xlabel('Datetime')
# ax.set_title('Time coverage of Z01, Z02, ASSIST, and Doppler Datasets')
# ax.grid(axis='x', alpha=0.3)
# ax.legend(loc='upper right')
# plt.tight_layout()
# plt.show()
####################################################################
# With all of the datasets aligned in UTC now it's time to make a wind profile plots
## With the Z01, Z02, and the ddoppler (April and May) datasets, we can create wind profile plots
# make the hegith of the wind speed profile plot up to 500 m
MAX_ALT = 500          # m

#For April events use the following exact time in UTC:
# First group of extreme event times 
## APRIL 23 00:00 UTC
## APRIL 23 06:00 UTC
## APRIL 23 07:00 UTC
## APRIL 23 14:00 UTC
## APRIL 23 15:00 UTC
## APRIL 23 16:00 UTC
## APRIL 23 17:00 UTC

# For May events use the following exact time in UTC:
# First group of extreme event times 
## MAY 7 08:00 UTC
## MAY 7 09:00 UTC
## MAY 7 13:00 UTC
## MAY 7 15:00 UTC

event_days = {
    'April 23': [
        '2026-04-23 00:00',
        '2026-04-23 06:00',
        '2026-04-23 07:00',
        '2026-04-23 14:00',
        '2026-04-23 15:00',
        '2026-04-23 16:00',
        '2026-04-23 17:00'
    ],
    'May 7': [
        '2026-05-07 08:00',
        '2026-05-07 09:00',
        '2026-05-07 13:00',
        '2026-05-07 15:00'
    ]
}

# Use the nearest observation within 30 minutes, preserving the actual sample time.
TOL = pd.Timedelta('30min')

# def nearest_profile(ds, target):
#     times = pd.DatetimeIndex(pd.to_datetime(ds['time'].values))
#     valid_positions = np.flatnonzero(~times.isna())
#     if not valid_positions.size:
#         return None, None
#     valid_times = times[valid_positions]
#     position = np.abs(valid_times - target).argmin()
#     if abs(valid_times[position] - target) > TOL:
#         return None, None
#     return ds.isel(time=valid_positions[position]), valid_times[position]

# doppler_by_day = {'April 23': ds_dp1, 'May 7': ds_dp2}

# # one figure per event day, one subplot per event time
# for day_label, day_times in event_days.items():
#     n = len(day_times)
#     ncols = min(n, 3)
#     nrows = int(np.ceil(n / ncols))
#     fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 5 * nrows),
#                              sharex=True, sharey=True, squeeze=False)
#     for ax, event_time in zip(axes.flat, day_times):
#         target = pd.Timestamp(event_time)
#         sources = [
#             ('Z01', ds_z01, 'WS', 'height', 'blue'),
#             ('Z02', ds_z02, 'wind_speed', 'distance', 'red'),
#             ('Dual Doppler', doppler_by_day[day_label], 'WS_filtered', 'z', 'green'),
#         ]
#         missing = []
#         for label, dataset, variable, height, color in sources:
#             scan, matched_time = nearest_profile(dataset, target)
#             if scan is None:
#                 missing.append(f'{label}: no sample within 30 min')
#                 continue
#             profile = scan[variable]
#             if label == 'Dual Doppler':
#                 profile = profile.mean(dim=['x', 'y'], skipna=True)
#             if not np.isfinite(profile.values).any():
#                 missing.append(f'{label}: no valid data')
#                 continue
#             ax.plot(profile.values, scan[height].values, color=color,
#                     label=f'{label} ({matched_time:%H:%M:%S} UTC)')
#         ax.set_title(f'{target:%H:%M} UTC')
#         ax.set_ylim(0, MAX_ALT)
#         ax.set_xlabel('Wind Speed [m/s]')
#         ax.grid(True, alpha=0.2, ls='--')
#         if ax.lines:
#             ax.legend(fontsize=8)
#         if missing:
#             ax.text(0.02, 0.98, '\n'.join(missing), transform=ax.transAxes,
#                     va='top', fontsize=8)
#     for ax in axes.flat[n:]:
#         ax.set_visible(False)
#     for ax in axes[:, 0]:
#         ax.set_ylabel('Height [m]')
#     fig.suptitle(f'Wind Speed Profiles - {day_label}')
#     fig.tight_layout(rect=(0, 0, 1, 0.95))
#     plt.subplots_adjust(hspace=0.4)
#     plt.show()


#################################################################### 
# Now that we can see the periods where there is a time agreement between the datasets, we can proceed with further analysis.
# Now we can work on crating shared temperature (from the assist) and the wind profiles (from z01 and z02) during an exact time

# First group of extreme event times 
## APRIL 23 00:00 UTC
## APRIL 23 06:00 UTC
## APRIL 23 07:00 UTC
## APRIL 23 14:00 UTC
## APRIL 23 15:00 UTC
## APRIL 23 16:00 UTC
## APRIL 23 17:00 UTC

#SECOND group of extreme event times 
## MAY 7 08:00 UTC
## MAY 7 09:00 UTC
## MAY 7 13:00 UTC
## MAY 7 15:00 UTC



# Build the profile plots: one figure per event group, one subplot per time.
# Temperature (ASSIST) on the bottom axis, wind speed (Z01 and Z02) on the top axis.
#set the use the temperature from the ASSIST dataset to have the range of -10 t0 20 C 
#for a more consistent comparison with the wind profiles

MAX_ALT = 1000          # m
TOL = pd.Timedelta('30min')   # max gap allowed between requested and nearest sample
TEMP_LIMITS = (-10, 20)  # deg C, shared by every subplot

event_groups = {
    'April 23, 2026': [f'2026-04-23 {h}:00' for h in ('00', '06', '07', '14', '15', '16', '17')],
    'May 7, 2026':    [f'2026-05-07 {h}:00' for h in ('08', '09', '13', '15')],
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
        ax.set_xlim(*TEMP_LIMITS)
        ax.set_ylabel('Altitude (m)')
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.set_title(f'{target:%H:%M} UTC', pad=55)

        temp_message = None
        if at is not None:
            h = at['height'].values * 1000   # km -> m
            temperature = at['temperature'].values
            visible = np.isfinite(temperature) & np.isfinite(h) & (h >= 0) & (h <= MAX_ALT)
            if visible.any():
                ax.plot(temperature, h, color=temp_color, lw=2.5, label='ASSIST temp')
                if np.any((temperature[visible] < TEMP_LIMITS[0]) | (temperature[visible] > TEMP_LIMITS[1])):
                    temp_message = 'Temperature extends outside axis limits'
            else:
                temp_message = 'No valid ASSIST temperature below 1000 m'
        else:
            temp_message = 'No ASSIST sample within 30 min'
        if temp_message:
            ax.text(0.02, 0.98, temp_message, transform=ax.transAxes,
                    va='top', fontsize=8, color=temp_color)
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
    fig.tight_layout(h_pad=5, w_pad=3, rect=(0, 0, 1, 0.92))

for title, times in event_groups.items():
    plot_event_group(title, times)
plt.show()
##################################################
