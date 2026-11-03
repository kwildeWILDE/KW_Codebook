#import necessary libraries
from statistics import LinearRegression
from webbrowser import get

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
import re
#####################################################

#Pull the M2 data from the directory
#Note that this data only contains the temperature varaibles (and the data quality flags)

dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
files_m2 = f'{dp_m2}/M2_FULL_JAN31_OCT31_2026_Datapull.xlsx'

#Read the M2 files
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = files_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(files_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(files_m2)
    ds_m2.to_pickle(cache_m2)

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

# Apply the flat run mask to the temperature columns in the M2 dataset
ds_m2_filtered = ds_m2.copy()
for col in ["Temperature @ 2m [deg C]", "Temperature @ 50m [deg C]", "Temperature @ 80m [deg C]"]:
    if col in ds_m2_filtered.columns:
        #the status-code filter doesn't catch sensor fill values (e.g. -300), so also reject non-physical temperatures
        ds_m2_filtered[col] = ds_m2_filtered[col].where(ds_m2_filtered[col].between(-50, 50))
        ds_m2_filtered[col] = mask_flat_runs(ds_m2_filtered[col])

#############################################################
#Pull the ASSIST data from the directory

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
#print(ds_at_filtered)
###################################################################################
# Print a list of available heights that have temperature data in the ASSIST dataset
#count the valid values at every height in one pass; .compute() turns the dask result into numpy
#convert the height from km to m for easier interpretation

valid_counts = ds_at_filtered['temperature'].notnull().sum(dim='time').compute()
valid_counts['height'] = valid_counts['height'] * 1000

for height, valid_count in zip(valid_counts['height'].values, valid_counts.values):
    if valid_count > 0:
        print(f"Height: {height} m, Number of temperature measurements: {valid_count}")

######################
# Make the varibles for the temperature at for the M2 dataset at specific heights
m2_temp_2m = ds_m2_filtered["Temperature @ 2m [deg C]"]
m2_temp_50m = ds_m2_filtered["Temperature @ 50m [deg C]"]
#m2_temp_80m = ds_m2_filtered["Temperature @ 80m [deg C]"]

##
#make the varibles for the temperature at specific heights (close to the M2 heights) from the ASSIST dataset
at_temp_0m = ds_at_filtered['temperature'].sel(height=0.00, method='nearest')
at_temp_46m = ds_at_filtered['temperature'].sel(height=0.046, method='nearest')
at_temp_61m = ds_at_filtered['temperature'].sel(height=0.061, method='nearest')

#### 
#Make a linear regression between the M2 and ASSIST temperatures with near corresponding heights 
# Height comparison between M2 and ASSIST datasets for linear regression 
#2m M2 and 0m ASSIST ;
#50m M2 and 46m ASSIST ;
#80m M2 and 61m ASSIST ;

m2_temp_by_height = {
    2: m2_temp_2m,
    50: m2_temp_50m,
}

at_temp_by_height = {
    0: at_temp_0m,
    46: at_temp_46m,
    61: at_temp_61m,
}

height_pairs = [
    (2, 0),
    (50, 46),
    (80, 61)
]

# Only plot pairs where both datasets have data (M2 80m is currently excluded)
plot_pairs = [(m, a) for m, a in height_pairs if m in m2_temp_by_height and a in at_temp_by_height]
skipped = [p for p in height_pairs if p not in plot_pairs]
if skipped:
    print(f"Skipping height pairs with no data loaded (M2 m, ASSIST m): {skipped}")

# Match the datasets on UTC time. Two methods are compared:
#  - nearest (not interpolated): each ASSIST sample is paired with the nearest M2 sample in time
#  - linear (interpolated): M2 is linearly interpolated in time onto each ASSIST timestamp, using the
#    M2 samples on either side (dropped if either is more than MATCH_TOLERANCE away, so no gaps are bridged)
MATCH_TOLERANCE = pd.Timedelta(minutes=5)

# def match_on_utc(m2_series, at_series, method='linear'):
#     m2_df = (pd.DataFrame({'UTC_time': ds_m2_filtered['UTC_time'], 'm2': m2_series})
#              .dropna().drop_duplicates(subset='UTC_time').sort_values('UTC_time'))
#     at_vals = at_series.load()
#     at_df = (pd.DataFrame({'UTC_time': pd.to_datetime(at_vals['time'].values), 'at': at_vals.values})
#              .dropna().drop_duplicates(subset='UTC_time').sort_values('UTC_time'))
#     #the two time columns can have different datetime units (ns vs us), so cast both to ns
#     m2_df['UTC_time'] = m2_df['UTC_time'].astype('datetime64[ns]')
#     at_df['UTC_time'] = at_df['UTC_time'].astype('datetime64[ns]')
#     if method == 'nearest':
#         merged = pd.merge_asof(at_df, m2_df, on='UTC_time', direction='nearest', tolerance=MATCH_TOLERANCE)
#         return merged.dropna()
#     m2_t = m2_df['UTC_time'].to_numpy().astype('int64')
#     at_t = at_df['UTC_time'].to_numpy().astype('int64')
#     tol = MATCH_TOLERANCE.value
#     idx = np.searchsorted(m2_t, at_t)
#     ok = (idx > 0) & (idx < m2_t.size)
#     lo, hi = np.clip(idx - 1, 0, m2_t.size - 1), np.clip(idx, 0, m2_t.size - 1)
#     ok &= ((at_t - m2_t[lo]) <= tol) & ((m2_t[hi] - at_t) <= tol)
#     out = at_df.loc[ok].copy()
#     out['m2'] = np.interp(at_t[ok], m2_t, m2_df['m2'].to_numpy())
#     return out.dropna()

# # Left column: NOT interpolated (nearest ASSIST level in height, nearest M2 sample in time)
# # Right column: linearly interpolated (ASSIST interpolated in height to the M2 sensor height, M2 interpolated in time)
# at_interp_by_height = {m: ds_at_filtered['temperature'].interp(height=m / 1000) for m in m2_temp_by_height}
# modes = [('nearest', 'Not interpolated (nearest level and time)', at_temp_by_height),
#          ('linear', 'Linearly interpolated (height and time)', at_interp_by_height)]

# fig, axes = plt.subplots(len(plot_pairs), 2, figsize=(14, 5 * len(plot_pairs)), squeeze=False)
# for row, (m2_height, at_height) in zip(axes, plot_pairs):
#     for ax, (method, title, at_source) in zip(row, modes):
#         at_key = at_height if method == 'nearest' else m2_height
#         matched = match_on_utc(m2_temp_by_height[m2_height], at_source[at_key], method)
#         x, y = matched['m2'].values, matched['at'].values
#         ax.scatter(x, y, s=5, alpha=0.3, color='steelblue')
#         if x.size > 1:
#             slope, intercept, r, p, se = stats.linregress(x, y)
#             xs = np.linspace(x.min(), x.max(), 200)
#             ax.plot(xs, slope * xs + intercept, color='red', lw=2,
#                     label=f'y = {slope:.3f}x + {intercept:.3f}\n$R^2$ = {r**2:.4f}, n = {x.size}')
#             ax.legend(loc='upper left')
#             print(f"M2 {m2_height}m, {method}: slope {slope:.4f}, intercept {intercept:.4f}, R2 {r**2:.4f}, n {x.size}")
#         ax.set_xlabel(f'M2 Temperature at {m2_height}m [deg C]')
#         ax.set_ylabel(f'ASSIST Temperature at {at_key}m [deg C]')
#         ax.set_title(f'M2 {m2_height}m: {title}', fontsize=10)
#         ax.grid(True, alpha=0.2, ls='--')
# plt.tight_layout()
# plt.show()
####################################################################################
#Now that we have the filtered M2 and ASSIST datasets, 
#We can now create the necessary plots to find the agreement in tempature from both datasets

# Main goal plot:
#create a month to month temperature over height heat map (ASSIST) with the scattered M2 temperature points overlaid
#for the height range being 0-100 (for the ASSIST)
#and the scatter points from the M2 being at heights of 2, and 50m (only heights available in the dataset)
#superimpose the M2 scatter points on top of the ASSIST heat map

#create the varaibles for temperature at certain heights from the M2 dataset
m2_temp_2m =ds_m2_filtered["Temperature @ 2m [deg C]"]
m2_temp_50m =ds_m2_filtered["Temperature @ 50m [deg C]"]

#create a variable for the ASSIST temperature profile from 0 to 100m
#ASSIST height is in km, so 0-100 m is 0-0.1 km
at_temp_0_100m = ds_at_filtered['temperature'].sel(height=slice(0, 0.1))

# When plotting the scatter points from the M2, dataset make sure the heights 
#have their corresponding color based on the height they represent 
#define the colors for each height
height_colors = {
    2: 'cyan',
    50: 'tomato',
}

#make sure that the time varaible between M2 and ASSIST datasets are aligned
#make sure they have the same variable for the month of the year


# Now try to make a month by month (late FEB - late JUN) temperature over height heat map (from the ASSIST dataset) 
# with M2 scatter points
import matplotlib.pyplot as plt

months = [2, 3, 4, 5, 6]  # late February to late June

#load the small 0-200m ASSIST subset into memory so boolean masks can be used (dask arrays can't be indexed by boolean dask arrays)
at_temp_0_100m = at_temp_0_100m.load()
at_temp_0_100m = at_temp_0_100m.where((at_temp_0_100m > -50) & (at_temp_0_100m < 50))
at_months = at_temp_0_100m['time'].dt.month.values
m2_months = ds_m2_filtered['UTC_time'].dt.month

# for month in months:
#     #filter the ASSIST and M2 datasets for the current month
#     print(f"Processing month: {month}")
#     at_temp_0_100m_month = at_temp_0_100m.isel(time=np.where(at_months == month)[0])
#     m2_month = ds_m2_filtered[m2_months == month]
#     m2_temp_2m_month = m2_month.set_index('UTC_time')["Temperature @ 2m [deg C]"]
#     m2_temp_50m_month = m2_month.set_index('UTC_time')["Temperature @ 50m [deg C]"]
#     # print(f"ASSIST data points for month {month}: {len(at_temp_0_200m_month['time'])}")
#     # print(f"M2 2m data points for month {month}: {len(m2_temp_2m_month['time'])}")
#     # print(f"M2 50m data points for month {month}: {len(m2_temp_50m_month['time'])}")
#     # print(f"M2 80m data points for month {month}: {len(m2_temp_80m_month['time'])}")
#     #create the figure and axis
#     fig, ax = plt.subplots(figsize=(12, 6))

#     #plot the ASSIST temperature profile as a heat map
#     #the M2 points are drawn on the same axis at their measurement heights and colored with the
#     #same colormap and limits as the heat map, so equal colors mean equal temperatures
#     #only keep valid M2 measurements
#     m2_2m_valid = m2_temp_2m_month[m2_temp_2m_month > -20]
#     m2_50m_valid = m2_temp_50m_month[m2_temp_50m_month > -20]
#     vmin = np.nanmin([float(at_temp_0_100m_month.min()), m2_2m_valid.min(), m2_50m_valid.min()])
#     vmax = np.nanmax([float(at_temp_0_100m_month.max()), m2_2m_valid.max(), m2_50m_valid.max()])

#     pcm = ax.pcolormesh(at_temp_0_100m_month['time'], at_temp_0_100m_month['height'] * 1000, at_temp_0_100m_month.T,
#                         shading='auto', cmap='viridis', vmin=vmin, vmax=vmax)
#     fig.colorbar(pcm, ax=ax, label='Temperature [deg C] (ASSIST heat map and M2 points)')

#     for m2_h, m2_valid in [(2, m2_2m_valid), (50, m2_50m_valid)]:
#         ax.scatter(m2_valid.index, np.full(len(m2_valid), m2_h), c=m2_valid.values, cmap='viridis',
#                    vmin=vmin, vmax=vmax, s=20, edgecolors='k', linewidths=0.2, zorder=3)
#         ax.axhline(m2_h, color='k', lw=0.4, ls=':', alpha=0.6)
#         ax.annotate(f'M2 {m2_h}m', xy=(1.0, m2_h), xycoords=('axes fraction', 'data'),
#                     xytext=(-4, 3), textcoords='offset points', ha='right', fontsize=8,
#                     bbox=dict(facecolor='white', alpha=0.7, pad=1))

#     ax.set_ylim(0, 100)
#     ax.set_xlabel('Time (UTC)')
#     ax.set_ylabel('Height [m]')
#     plt.title(f'ASSIST Temperature over Height with Superimposed M2 Points for month {month}, 2026')
#     plt.tight_layout()
#     plt.show()

# Note: The 80m M2 temperature data has been poorly recored there and is therefore not included in the plots.#### 
#Have not saved the plots with the max height of 100m 
##########################################################################
## Create a month to month dirunal average of the temperature profiles with the ASSIST and M2 data 
#superimpose the M2 data on the ASSIST temperature profiles at the sensor heights (2m, 50m)
#also show the planatry boundry layer height change over day from the Assist dataset


# Diurnal averages are computed in MST (UTC-7) local time, the same clock the M2 data is recorded in
at_local = pd.to_datetime(at_temp_0_100m['time'].values) - pd.Timedelta(hours=7)
at_hours = np.asarray(at_local.hour)
at_local_months = np.asarray(at_local.month)

m2_local = ds_m2_filtered['UTC_time'] - pd.Timedelta(hours=7)
m2_diurnal_src = pd.DataFrame({
    'month': m2_local.dt.month,
    'hour': m2_local.dt.hour,
    2: ds_m2_filtered["Temperature @ 2m [deg C]"],
    50: ds_m2_filtered["Temperature @ 50m [deg C]"],
})
m2_diurnal = m2_diurnal_src.groupby(['month', 'hour']).mean()

month_names = {2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June'}
at_heights_m = at_temp_0_100m['height'].values * 1000

#hourly-mean ASSIST profile for every month: (hour, height)
at_diurnal = {}
for month in months:
    sel = at_local_months == month
    profile = np.full((24, at_heights_m.size), np.nan)
    for hr in range(24):
        hr_sel = sel & (at_hours == hr)
        if hr_sel.any():
            profile[hr] = np.nanmean(at_temp_0_100m.values[hr_sel], axis=0)
    at_diurnal[month] = profile

#one shared color scale so the months and the M2 points are directly comparable
vmin = np.nanmin([np.nanmin(p) for p in at_diurnal.values()] + [m2_diurnal[[2, 50]].min().min()])
vmax = np.nanmax([np.nanmax(p) for p in at_diurnal.values()] + [m2_diurnal[[2, 50]].max().max()])
levels = np.linspace(vmin, vmax, 21)

# fig, axes = plt.subplots(1, len(months), figsize=(4 * len(months), 4.5), sharey=True, constrained_layout=True)
# hours = np.arange(24)
# for ax, month in zip(axes, months):
#     cf = ax.contourf(hours, at_heights_m, at_diurnal[month].T, levels=levels, cmap='RdYlBu_r', extend='both')
#     ax.contour(hours, at_heights_m, at_diurnal[month].T, levels=levels[::4], colors='k', linewidths=0.5)

#     #M2 diurnal mean at the sensor heights, drawn with the same colormap so matching colors = agreement
#     for m2_h in (2, 50):
#         if month in m2_diurnal.index.get_level_values('month'):
#             m2_m = m2_diurnal.loc[month][m2_h].dropna()
#             ax.scatter(m2_m.index, np.full(len(m2_m), m2_h), c=m2_m.values, cmap='RdYlBu_r',
#                        vmin=vmin, vmax=vmax, s=45, edgecolors=height_colors[m2_h], linewidths=1.2, zorder=3)
#         ax.axhline(m2_h, color=height_colors[m2_h], lw=0.6, ls=':')

#     ax.set_title(month_names[month])
#     ax.set_xlim(0, 23)
#     ax.set_ylim(0, 100)
#     ax.set_xticks([0, 6, 12, 18])
#     ax.set_xlabel('Time (MST)')
#     ax.grid(True, alpha=0.2, ls='--')
# axes[0].set_ylabel('Height [m]')
# fig.colorbar(cf, ax=axes, label='Temperature [deg C]')
# fig.text(0.5, 0.01, 'M2 circles: cyan outline = 2 m, tomato outline = 50 m', ha='center', fontsize=9)
# fig.suptitle('Diurnal mean temperature: ASSIST profile with M2 at 2 m and 50 m')
# plt.show()

# #numeric agreement (ASSIST nearest level minus M2) per month, averaged over the diurnal cycle
# for month in months:
#     for m2_h, at_h in [(2, 0), (50, 46)]:
#         k = np.argmin(np.abs(at_heights_m - at_h))
#         if month in m2_diurnal.index.get_level_values('month'):
#             m2_m = m2_diurnal.loc[month][m2_h].reindex(hours).values
#             diff = at_diurnal[month][:, k] - m2_m
#             print(f"{month_names[month]} M2 {m2_h}m vs ASSIST {at_h}m: mean bias {np.nanmean(diff):.2f} C, RMSE {np.sqrt(np.nanmean(diff**2)):.2f} C")

################################################################################
# after some analysis we have times and dates of when extreme events are happening
# with the assist dataset, make make a tempature profile for that exact time and date 

# First group of extreme event times 
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

#print the head of the at dataset to see the layout of the time variable 
# print(ds_at_filtered.head())
# print (ds_at_filtered['time'])
# adjust the time format to make it easier to select specific times for extreme events
ds_at_filtered['time'] = pd.to_datetime(ds_at_filtered['time'].values)
print(ds_at_filtered['time'])

# With the amount of extreme events, we can loop through these times and generate temperature profiles for each one
extreme_event_times = [
    '2026-04-23 07:00',
    '2026-04-23 14:00',
    '2026-04-23 15:00',
    '2026-04-23 16:00',
    '2026-04-23 17:00',
    '2026-05-07 08:00',
    '2026-05-07 09:00',
    '2026-05-07 13:00',
    '2026-05-07 15:00',
]

for event_time in extreme_event_times:
    event_dt = pd.to_datetime(event_time)
    profile = ds_at_filtered.sel(time=event_dt, method='nearest')
    plt.figure(figsize=(4, 6))
    plt.plot(profile['temperature'], profile['height'])
    plt.xlabel('Temperature [deg C]')
    plt.ylabel('Height [km]')
    plt.title(f'Temperature profile at {event_time} UTC')
    plt.grid(True, alpha=0.2, ls='--')
    plt.tight_layout()
    plt.show()

######################################################### 