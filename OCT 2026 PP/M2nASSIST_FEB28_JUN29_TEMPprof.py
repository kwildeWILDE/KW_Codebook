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

# Match the datasets on UTC time. ASSIST and M2 sampling differ, so each ASSIST sample is
# paired with the nearest M2 sample within a tolerance (rows without a match are dropped).
MATCH_TOLERANCE = pd.Timedelta(minutes=5)

def match_on_utc(m2_series, at_series):
    m2_df = (pd.DataFrame({'UTC_time': ds_m2_filtered['UTC_time'], 'm2': m2_series})
             .dropna().drop_duplicates(subset='UTC_time').sort_values('UTC_time'))
    at_vals = at_series.load()
    at_df = (pd.DataFrame({'UTC_time': pd.to_datetime(at_vals['time'].values), 'at': at_vals.values})
             .dropna().drop_duplicates(subset='UTC_time').sort_values('UTC_time'))
    #the two time columns can have different datetime units (ns vs us), so cast both to ns
    m2_df['UTC_time'] = m2_df['UTC_time'].astype('datetime64[ns]')
    at_df['UTC_time'] = at_df['UTC_time'].astype('datetime64[ns]')
    merged = pd.merge_asof(at_df, m2_df, on='UTC_time', direction='nearest', tolerance=MATCH_TOLERANCE)
    return merged.dropna()

# create subplots for each height pairs for the linear regression 
# fig, axes = plt.subplots(len(plot_pairs), 1, figsize=(8, 5 * len(plot_pairs)), squeeze=False)
# for ax, (m2_height, at_height) in zip(axes.ravel(), plot_pairs):
#     matched = match_on_utc(m2_temp_by_height[m2_height], at_temp_by_height[at_height])
#     x, y = matched['m2'].values, matched['at'].values
#     ax.scatter(x, y, s=5, alpha=0.3, color='steelblue')
#     if x.size > 1:
#         slope, intercept, r, p, se = stats.linregress(x, y)
#         xs = np.linspace(x.min(), x.max(), 200)
#         ax.plot(xs, slope * xs + intercept, color='red', lw=2,
#                 label=f'y = {slope:.2f}x + {intercept:.2f}\n$R^2$ = {r**2:.3f}, n = {x.size}')
#         ax.legend(loc='upper left')
#     ax.set_xlabel(f'M2 Temperature at {m2_height}m [deg C]')
#     ax.set_ylabel(f'ASSIST Temperature at {at_height}m [deg C]')
#     ax.set_title(f'M2 {m2_height}m vs ASSIST {at_height}m (UTC-matched)')
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
at_months = at_temp_0_100m['time'].dt.month.values
m2_months = ds_m2_filtered['UTC_time'].dt.month

for month in months:
    #filter the ASSIST and M2 datasets for the current month
    print(f"Processing month: {month}")
    at_temp_0_100m_month = at_temp_0_100m.isel(time=np.where(at_months == month)[0])
    m2_month = ds_m2_filtered[m2_months == month]
    m2_temp_2m_month = m2_month.set_index('UTC_time')["Temperature @ 2m [deg C]"]
    m2_temp_50m_month = m2_month.set_index('UTC_time')["Temperature @ 50m [deg C]"]
    # print(f"ASSIST data points for month {month}: {len(at_temp_0_200m_month['time'])}")
    # print(f"M2 2m data points for month {month}: {len(m2_temp_2m_month['time'])}")
    # print(f"M2 50m data points for month {month}: {len(m2_temp_50m_month['time'])}")
    # print(f"M2 80m data points for month {month}: {len(m2_temp_80m_month['time'])}")
    #create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    #plot the ASSIST temperature profile as a heat map
    #the M2 points are drawn on the same axis at their measurement heights and colored with the
    #same colormap and limits as the heat map, so equal colors mean equal temperatures
    #only keep valid M2 measurements
    m2_2m_valid = m2_temp_2m_month[m2_temp_2m_month > -20]
    m2_50m_valid = m2_temp_50m_month[m2_temp_50m_month > -20]
    vmin = np.nanmin([float(at_temp_0_100m_month.min()), m2_2m_valid.min(), m2_50m_valid.min()])
    vmax = np.nanmax([float(at_temp_0_100m_month.max()), m2_2m_valid.max(), m2_50m_valid.max()])

    pcm = ax.pcolormesh(at_temp_0_100m_month['time'], at_temp_0_100m_month['height'] * 1000, at_temp_0_100m_month.T,
                        shading='auto', cmap='viridis', vmin=vmin, vmax=vmax)
    fig.colorbar(pcm, ax=ax, label='Temperature [deg C] (ASSIST heat map and M2 points)')

    for m2_h, m2_valid in [(2, m2_2m_valid), (50, m2_50m_valid)]:
        ax.scatter(m2_valid.index, np.full(len(m2_valid), m2_h), c=m2_valid.values, cmap='viridis',
                   vmin=vmin, vmax=vmax, s=20, edgecolors='k', linewidths=0.2, zorder=3)
        ax.axhline(m2_h, color='k', lw=0.4, ls=':', alpha=0.6)
        ax.annotate(f'M2 {m2_h}m', xy=(1.0, m2_h), xycoords=('axes fraction', 'data'),
                    xytext=(-4, 3), textcoords='offset points', ha='right', fontsize=8,
                    bbox=dict(facecolor='white', alpha=0.7, pad=1))

    ax.set_ylim(0, 100)
    ax.set_xlabel('Time (UTC)')
    ax.set_ylabel('Height [m]')
    plt.title(f'ASSIST Temperature over Height with Superimposed M2 Points for month {month}, 2026')
    plt.tight_layout()
    plt.show()

# Note: The 80m M2 temperature data has been poorly recored there and is therefore not included in the plots.#### 
#Have not saved the plots with the max height of 100m 

