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
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator
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
## Use the selected six-hour offset to convert the recorded M2 times to UTC.
ds_m2['DS_time'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + ds_m2['MST'].astype(str))
ds_m2['UTC_time'] = ds_m2['DS_time'] + pd.Timedelta(hours=6)

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
temperature_columns = [
    col for col in ["Temperature @ 2m [deg C]", "Temperature @ 50m [deg C]", "Temperature @ 80m [deg C]"]
    if col in ds_m2_filtered.columns
]
for col in temperature_columns:
    #the status-code filter doesn't catch sensor fill values (e.g. -300), so also reject non-physical temperatures
    ds_m2_filtered[col] = ds_m2_filtered[col].where(ds_m2_filtered[col].between(-50, 50))
    ds_m2_filtered[col] = mask_flat_runs(ds_m2_filtered[col])

# Keep UTC_time as a column for the matching and plotting code below.
ds_m2_filtered = (
    ds_m2_filtered.resample('10min', on='UTC_time')[temperature_columns]
    .mean()
    .reset_index()
)

print("M2 dataset successfully flat-run filtered and resampled to 10-minute intervals.")

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

# Compare each M2 sensor with the nearest available ASSIST height, without interpolating.
m2_temp_by_height = {
    2: m2_temp_2m,
    50: m2_temp_50m,
}

# Pair each ASSIST sample with the nearest valid M2 sample within five minutes.
MATCH_TOLERANCE = pd.Timedelta(minutes=5)

# def match_on_utc(m2_series, at_series):
#     m2_df = (pd.DataFrame({'UTC_time': ds_m2_filtered['UTC_time'], 'm2': m2_series})
#              .dropna().drop_duplicates(subset='UTC_time').sort_values('UTC_time'))
#     at_vals = at_series.load()
#     at_df = (pd.DataFrame({'UTC_time': pd.to_datetime(at_vals['time'].values), 'at': at_vals.values})
#              .dropna().drop_duplicates(subset='UTC_time').sort_values('UTC_time'))
#     #the two time columns can have different datetime units (ns vs us), so cast both to ns
#     m2_df['UTC_time'] = m2_df['UTC_time'].astype('datetime64[ns]')
#     at_df['UTC_time'] = at_df['UTC_time'].astype('datetime64[ns]')
#     merged = pd.merge_asof(at_df, m2_df, on='UTC_time', direction='nearest', tolerance=MATCH_TOLERANCE)
#     return merged.dropna()

# fig, axes = plt.subplots(1, 2, figsize=(12, 6), squeeze=False)
# for ax, (m2_height, m2_temp) in zip(axes[0], m2_temp_by_height.items()):
#     at_temp = ds_at_filtered['temperature'].sel(height=m2_height / 1000, method='nearest')
#     at_height = float(at_temp['height'].values) * 1000
#     matched = match_on_utc(m2_temp, at_temp)
#     x, y = matched['m2'].values, matched['at'].values
#     ax.scatter(x, y, s=5, alpha=0.3, color='steelblue')
#     if x.size > 1 and np.ptp(x) > 0:
#         slope, intercept, r, p, se = stats.linregress(x, y)
#         xs = np.linspace(x.min(), x.max(), 200)
#         ax.plot(xs, slope * xs + intercept, color='red', lw=2,
#                 label=f'y = {slope:.3f}x + {intercept:.3f}\n$R^2$ = {r**2:.4f}, n = {x.size}')
#         ax.legend(loc='upper left')
#         print(f"M2 {m2_height}m vs ASSIST {at_height:g}m: slope {slope:.4f}, intercept {intercept:.4f}, R2 {r**2:.4f}, n {x.size}")
#     else:
#         print(f"Cannot fit M2 {m2_height}m vs ASSIST {at_height:g}m: not enough distinct matched M2 temperatures (n = {x.size}).")
#     ax.set_xlabel(f'M2 Temperature at {m2_height}m [deg C]')
#     ax.set_ylabel(f'ASSIST Temperature at {at_height:g}m [deg C]')
#     ax.set_title(f'M2 (10-min interval) {m2_height}m vs ASSIST {at_height:g}m', fontsize=10)
#     ax.set_box_aspect(1)
#     ax.grid(True, alpha=0.2, ls='--')
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
## Monthly diurnal temperature profiles in UTC, with M2 at 2 m and 50 m.
at_temp_0_2000m = ds_at_filtered['temperature'].sel(height=slice(0, 2.0)).load()
at_temp_0_2000m = at_temp_0_2000m.where((at_temp_0_2000m > -50) & (at_temp_0_2000m < 50))
at_utc = pd.to_datetime(at_temp_0_2000m['time'].values)
at_heights_2000m = at_temp_0_2000m['height'].values * 1000
at_heights_m = at_temp_0_100m['height'].values * 1000
hours = np.arange(24)

at_diurnal_src = pd.DataFrame(
    at_temp_0_2000m.values,
    index=pd.MultiIndex.from_arrays([at_utc.month, at_utc.hour], names=['month', 'hour']),
)
at_diurnal_means = at_diurnal_src.groupby(level=['month', 'hour']).mean()
at_diurnal_means = at_diurnal_means.reindex(pd.MultiIndex.from_product([months, hours], names=['month', 'hour']))
at_diurnal_2000m = {
    month: at_diurnal_means.loc[month].to_numpy() for month in months
}
at_diurnal = {
    month: profile[:, at_heights_2000m <= 100] for month, profile in at_diurnal_2000m.items()
}

m2_utc = ds_m2_filtered['UTC_time']
m2_diurnal_src = pd.DataFrame({
    'month': m2_utc.dt.month,
    'hour': m2_utc.dt.hour,
    2: ds_m2_filtered["Temperature @ 2m [deg C]"],
    50: ds_m2_filtered["Temperature @ 50m [deg C]"],
})
m2_diurnal = m2_diurnal_src.groupby(['month', 'hour']).mean()

month_names = {2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June'}

# One shared color scale for both height ranges, all months, and the M2 points.
plot_values = np.concatenate(
    [profile.ravel() for profile in at_diurnal_2000m.values()]
    + [m2_diurnal.loc[m2_diurnal.index.get_level_values('month').isin(months), [2, 50]].to_numpy().ravel()]
)
plot_values = plot_values[np.isfinite(plot_values)]
if plot_values.size == 0:
    raise ValueError("No valid M2 or ASSIST temperatures are available for the diurnal plots.")
vmin, vmax = plot_values.min(), plot_values.max()
if vmin == vmax:
    vmin, vmax = vmin - 0.5, vmax + 0.5
temperature_norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
temperature_cmap = 'RdYlBu_r'
contour_levels = plt.MaxNLocator(nbins=8).tick_values(vmin, vmax)

def smooth_contour_profile(profile):
    # Retain missing cells and wrap the diurnal hour when smoothing for display.
    valid = np.isfinite(profile)
    weights = gaussian_filter(valid.astype(float), sigma=(1, 0.75), mode=('wrap', 'nearest'))
    total = gaussian_filter(np.where(valid, profile, 0.0), sigma=(1, 0.75), mode=('wrap', 'nearest'))
    smoothed = np.full(profile.shape, np.nan)
    np.divide(total, weights, out=smoothed, where=valid & (weights > 0))
    return smoothed

fig, axes = plt.subplots(2, len(months), figsize=(4.3 * len(months), 10.5), sharex=True, constrained_layout=True)
fig.get_layout_engine().set(w_pad=0.1, h_pad=0.15, wspace=0.06, hspace=0.12)
for row, (heights, profiles, max_height) in enumerate([
    (at_heights_m, at_diurnal, 100),
    (at_heights_2000m, at_diurnal_2000m, 2000),
]):
    hour_edges = np.linspace(-0.5, 23.5, 97)
    height_edges = np.linspace(heights[0], heights[-1], 161)
    hour_centers = (hour_edges[:-1] + hour_edges[1:]) / 2
    height_centers = (height_edges[:-1] + height_edges[1:]) / 2
    hour_grid, height_grid = np.meshgrid(hour_centers, height_centers, indexing='ij')
    for ax, month in zip(axes[row], months):
        contour_profile = smooth_contour_profile(profiles[month])
        # Interpolate for display only, without filling missing values or extending beyond observed heights.
        cyclic_profile = np.concatenate((contour_profile[-1:], contour_profile, contour_profile[:1]), axis=0)
        interpolate = RegularGridInterpolator((np.arange(-1, 25), heights), cyclic_profile)
        heatmap_profile = interpolate((hour_grid, height_grid))
        heatmap = ax.pcolormesh(
            hour_edges, height_edges, heatmap_profile.T,
            cmap=temperature_cmap, norm=temperature_norm, shading='flat',
        )
        if np.isfinite(contour_profile).any():
            contours = ax.contour(
                hours, heights, contour_profile.T, levels=contour_levels,
                colors='black', linewidths=0.6, zorder=2,
            )
            ax.clabel(contours, inline=True, fontsize=7, fmt='%g')

        for m2_h in (2, 50):
            if month in m2_diurnal.index.get_level_values('month'):
                m2_m = m2_diurnal.loc[month][m2_h].dropna()
                ax.scatter(m2_m.index, np.full(len(m2_m), m2_h), c=m2_m.values,
                           cmap=temperature_cmap, norm=temperature_norm, s=45,
                           edgecolors=height_colors[m2_h], linewidths=1.2, zorder=3)
            ax.axhline(m2_h, color=height_colors[m2_h], lw=0.6, ls=':')

        ax.set_title(f'{month_names[month]} (0-{max_height} m)', pad=10)
        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(0, max_height)
        ax.set_xticks([0, 6, 12, 18])
        ax.set_xlabel('Time (UTC)', labelpad=8)
        ax.grid(True, alpha=0.2, ls='--')
    axes[row, 0].set_ylabel('Height [m]', labelpad=8)
fig.colorbar(heatmap, ax=axes, pad=0.02, label='Temperature [deg C] (ASSIST heat map and M2 points)')
fig.supxlabel('M2 circles: cyan outline = 2 m, tomato outline = 50 m; fill color = temperature', fontsize=9)
fig.suptitle('UTC diurnal mean temperature: ASSIST heat map and smoothed contours with M2 points', fontsize=14)
plt.show()

#numeric agreement (ASSIST nearest level minus M2) per month, averaged over the diurnal cycle
for month in months:
    for m2_h, at_h in [(2, 0), (50, 46)]:
        k = np.argmin(np.abs(at_heights_m - at_h))
        if month in m2_diurnal.index.get_level_values('month'):
            m2_m = m2_diurnal.loc[month][m2_h].reindex(hours).values
            diff = at_diurnal[month][:, k] - m2_m
            print(f"{month_names[month]} M2 {m2_h}m vs ASSIST {at_h}m: mean bias {np.nanmean(diff):.2f} C, RMSE {np.sqrt(np.nanmean(diff**2)):.2f} C")

################################################################################
# after some analysis we have times and dates of when extreme events are happening
# with the assist dataset, make make a tempature profile for that exact time and date 

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

#print the head of the at dataset to see the layout of the time variable 
# print(ds_at_filtered.head())
# print (ds_at_filtered['time'])
# adjust the time format to make it easier to select specific times for extreme events
ds_at_filtered['time'] = pd.to_datetime(ds_at_filtered['time'].values)
print(ds_at_filtered['time'])

# # Plot each month's extreme-event profiles together, with one subplot per time.
# extreme_event_times_by_month = {
#     'April 23, 2026': [
#         '2026-04-23 06:00',
#         '2026-04-23 13:00',
#         '2026-04-23 14:00',
#         '2026-04-23 15:00',
#         '2026-04-23 16:00',
#     ],
#     'May 7, 2026': [
#         '2026-05-07 07:00',
#         '2026-05-07 08:00',
#         '2026-05-07 12:00',
#         '2026-05-07 14:00',
#     ],
# }

# for month_label, event_times in extreme_event_times_by_month.items():
#     ncols = 2
#     nrows = (len(event_times) + ncols - 1) // ncols
#     fig, axes = plt.subplots(
#         nrows, ncols, figsize=(10, 4 * nrows), sharex=True, sharey=True, squeeze=False
#     )

#     for ax, event_time in zip(axes.flat, event_times):
#         event_dt = pd.to_datetime(event_time)
#         profile = ds_at_filtered.sel(time=event_dt, method='nearest')
#         profile_time = pd.to_datetime(profile['time'].values)
#         ax.plot(profile['temperature'], profile['height'])
#         ax.set_title(
#             f'Requested {event_dt:%H:%M} UTC\n'
#             f'Profile {profile_time:%H:%M} UTC'
#         )
#         ax.set_xlabel('Temperature [deg C]')
#         ax.set_ylabel('Height [km]')
#         ax.grid(True, alpha=0.2, ls='--')

#     for ax in axes.flat[len(event_times):]:
#         ax.set_visible(False)

#     fig.suptitle(f'ASSIST.TROpoeTemperature profiles during extreme events: {month_label}')
#     fig.tight_layout(rect=(0, 0, 1, 0.96))
#     plt.show()

######################################################### 