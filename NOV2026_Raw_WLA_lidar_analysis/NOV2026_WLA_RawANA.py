#import necessary libraries
from webbrowser import get
from datetime import timedelta, timezone

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
import xarray as xr
import glob
import os
import re
import warnings
import scipy.stats as stats
from scipy import stats
####################################
# Pulling the data from the WLS71460 lidar
dp_wls71 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/Raw_Lidar_NOV2026/WLS71460"
#there are two datasets from the WLS71460 lidar, one for each measurement period

# WLS71 dataset from Feb 16 to November 13 2026
dp_wls71_921 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/Raw_Lidar_NOV2026/WLS71460/WLS71460_2026_02_16_20261113-213921"

# WLS71data from Feb 16 to November 17 2026
dp_wls71_507 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/Raw_Lidar_NOV2026/WLS71460/WLS71460_2026_02_16_20261117-172507"

#the two datasets from the WLS71460 lidar are stored in dp_wls71_921 and dp_wls71_507 folders respectively 
#the files within the folders are .sta files 
#fully pull the data so that we can have all of the .sta files from both measurement periods for the wls71460 lidar
sta_files_wls71_921 = glob.glob(os.path.join(dp_wls71_921, '*.sta'))
sta_files_wls71_507 = glob.glob(os.path.join(dp_wls71_507, '*.sta'))

#combine all the .sta files into a single list
all_sta_files_wls71 = sta_files_wls71_921 + sta_files_wls71_507
print("Total number of .sta files for WLS71460 lidar:", len(all_sta_files_wls71))
#################
##############################################################################################
#################
#Pulling the data from the WLS73514 lidar
dp_wls73 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/Raw_Lidar_NOV2026/WLS73514"
#there are two datasets from the WLS73514 lidar, one for each measurement period

# WLS73 dataset from Feb 03 to November 13 2026
dp_wls73_921 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/Raw_Lidar_NOV2026/WLS73514/WLS73514_2026_02_03_20261113-213947"

# WLS73 dataset from March 12 to November 13 2026
dp_wls73_507 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/Raw_Lidar_NOV2026/WLS73514/WLS73514_2026_03_12_20261113-213938"

#fully pull the data so that we can have all of the .sta files from both measurement periods for the wls73514 lidar
sta_files_wls73_921 = glob.glob(os.path.join(dp_wls73_921, '*.sta'))
sta_files_wls73_507 = glob.glob(os.path.join(dp_wls73_507, '*.sta'))

#combine all the .sta files into a single list
all_sta_files_wls73 = sta_files_wls73_921 + sta_files_wls73_507
print("Total number of .sta files for WLS73514 lidar:", len(all_sta_files_wls73))
print(all_sta_files_wls73[:20])

#Print the heads of the first few .sta files for both lidars to inspect the data
print("WLS71460 first .sta file head:")
with open(all_sta_files_wls71[0], 'r', encoding='utf-8-sig') as f:
    for _ in range(10):
        print(f.readline().rstrip('\r\n'))

print("\nWLS73514 first .sta file head:")
with open(all_sta_files_wls73[0], 'r', encoding='utf-8-sig') as f:
    for _ in range(10):
        print(f.readline().rstrip('\r\n'))

#Print the coloumn names of the first .sta file for both lidars
print("WLS71460 first .sta file columns:")
with open(all_sta_files_wls71[0], 'r', encoding='utf-8-sig') as f:
    for line in f:
        if line.startswith('Timestamp (end of interval)'):
            print(line.rstrip('\r\n').split('\t'))
            break

print("\nWLS73514 first .sta file columns:")
with open(all_sta_files_wls73[0], 'r', encoding='utf-8-sig') as f:
    for line in f:
        if line.startswith('Timestamp (end of interval)'):
            print(line.rstrip('\r\n').split('\t'))
            break

##################################################################
#Now that we have pulled the data from both WLS71460 and WLS73514 lidars, we can proceed comparing the data quality from both lidar systems 

# First plotting the available data over the time for both lidar systems
#blue for WLS71460 lidar
#red for WLS73514 lidar
# The x-axis represents the timestamp in each .sta filename,
#  and the y-axis represents the separate WLS lidar systems (1 for WLS71460 and 2  for WLS73514).

# Plotting the number of .sta files over time for both lidar systems
times_wls71 = pd.to_datetime(
    [os.path.basename(path).split('_', 1)[1] for path in all_sta_files_wls71],
    format='%Y_%m_%d__%H_%M_%S.sta',
)
times_wls73 = pd.to_datetime(
    [os.path.basename(path).split('_', 1)[1] for path in all_sta_files_wls73],
    format='%Y_%m_%d__%H_%M_%S.sta',
)

def get_measurement_availability(sta_files, lidar):
    if not sta_files:
        raise ValueError(f"No .sta files found for {lidar}")

    frames = []
    for file_path in sta_files:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            file_timezone = None
            for line in f:
                if line.lower().startswith('timezone='):
                    if file_timezone is not None:
                        raise ValueError(f"Multiple timezones found in {file_path}")
                    value = line.split('=', 1)[1].strip()
                    match = re.fullmatch(r'UTC(?:([+-])(\d{1,2})(?::(\d{2}))?)?', value, re.IGNORECASE)
                    if not match:
                        raise ValueError(f"Invalid timezone {value!r} in {file_path}")
                    hours = int(match.group(2) or 0)
                    minutes = int(match.group(3) or 0)
                    if hours > 23 or minutes > 59:
                        raise ValueError(f"Invalid timezone {value!r} in {file_path}")
                    offset = timedelta(hours=hours, minutes=minutes)
                    file_timezone = timezone(-offset if match.group(1) == '-' else offset)
                if line.startswith('Timestamp (end of interval)'):
                    header = line.rstrip('\r\n').split('\t')
                    break
            else:
                raise ValueError(f"Measurement header not found in {file_path}")
            if file_timezone is None:
                raise ValueError(f"Timezone not found in {file_path}")

            speed_columns = {}
            for i, column in enumerate(header):
                match = re.fullmatch(r'(\d+)m Wind Speed \(m/s\)', column)
                if match:
                    speed_columns[int(match.group(1))] = i
            if not speed_columns:
                raise ValueError(f"No wind speed columns found in {file_path}")
            heights = sorted(speed_columns)
            availability_columns = []
            for height in heights:
                column = f'{height}m Data Availability (%)'
                if column not in header:
                    raise ValueError(f"Missing {column} in {file_path}")
                availability_columns.append(header.index(column))
            speed_indices = [speed_columns[height] for height in heights]
            data = pd.read_csv(
                f, sep='\t', header=None, names=range(len(header)),
                usecols=[0] + speed_indices + availability_columns,
            )

        measurement_times = pd.to_datetime(data[0], format='%Y/%m/%d %H:%M', errors='raise')
        if measurement_times.isna().any():
            raise ValueError(f"Missing measurement timestamp in {file_path}")
        measurement_times = measurement_times.dt.tz_localize(file_timezone).dt.tz_convert('UTC')
        speeds = data[speed_indices].apply(pd.to_numeric, errors='raise').to_numpy()
        availability = data[availability_columns].apply(pd.to_numeric, errors='raise').to_numpy()
        available = np.isfinite(speeds) & np.isfinite(availability) & (availability > 0)
        frame = pd.DataFrame(speeds, columns=heights)
        frame.insert(0, 'Timestamp', measurement_times)
        frame = frame.melt(id_vars='Timestamp', var_name='Height_m', value_name='WindSpeed')
        frame[lidar] = pd.DataFrame(available, columns=heights).melt(value_name=lidar)[lidar]
        frames.append(frame)

    result = pd.concat(frames, ignore_index=True)
    duplicates = result.duplicated(['Timestamp', 'Height_m'], keep=False)
    if duplicates.any():
        ambiguous_times = result.loc[duplicates, 'Timestamp'].unique()
        warnings.warn(
            f"Excluding {len(ambiguous_times)} ambiguous UTC timestamps for {lidar} "
            "with multiple measurements at the same height",
            stacklevel=2,
        )
        result = result.loc[~result['Timestamp'].isin(ambiguous_times)]
    return result


availability_wls71 = get_measurement_availability(all_sta_files_wls71, 'WLS71460')
availability_wls73 = get_measurement_availability(all_sta_files_wls73, 'WLS73514')
measurement_availability = availability_wls71.drop(columns='WindSpeed').merge(
    availability_wls73.drop(columns='WindSpeed'), on=['Timestamp', 'Height_m'], how='outer',
).sort_values(['Timestamp', 'Height_m'])

summary = pd.DataFrame({'Height_m': sorted(measurement_availability['Height_m'].unique())})
for lidar in ['WLS71460', 'WLS73514']:
    counts = measurement_availability.groupby('Height_m')[lidar].agg(['sum', 'count'])
    counts.columns = [f'{lidar}_available', f'{lidar}_recorded']
    summary = summary.merge(counts, on='Height_m', how='left')

# output_dir = os.path.dirname(os.path.abspath(__file__))
# measurement_availability.to_csv(os.path.join(output_dir, 'lidar_measurement_availability.csv'), index=False)
# summary.to_csv(os.path.join(output_dir, 'lidar_availability_by_height.csv'), index=False)
# print("Saved measurement availability and counts by height to", output_dir)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(times_wls71, [1]*len(times_wls71), 'bo', label='WLS71460')
ax.plot(times_wls73, [2]*len(times_wls73), 'ro', label='WLS73514')
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate()
plt.xlabel('Date')
plt.ylabel('Lidar System')
plt.title('Data Availability Over Time for WLS71460 and WLS73514 Lidars')
plt.legend()
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.4)
plt.tight_layout()
plt.show()

# Align file timestamps and indicate whether each lidar has a file at that timestamp.
timestamps = times_wls71.union(times_wls73).unique().sort_values()
# df_all = pd.DataFrame({
#     'Timestamp': timestamps,
#     'WLS71460': timestamps.isin(times_wls71),
#     'WLS73514': timestamps.isin(times_wls73),
# })
# df_all.to_csv('lidar_data_availability.csv', index=False)
# print("Lidar data availability saved to 'lidar_data_availability.csv'")


##########################################################################################
# see if we can make another plot that shows the overall time availability for the data and the different heights of the lidar measurements
# first see what heights are available in the .sta files for each lidar system
def get_heights_from_sta_files(sta_files):
    if not sta_files:
        raise ValueError("No .sta files were found to extract heights from.")

    heights = set()
    for file_path in sta_files:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if line.startswith('Altitudes AGL (m)='):
                    values = line.split('=', 1)[1].split()
                    if not values:
                        raise ValueError(f"No altitudes found in {file_path}")
                    try:
                        heights.update(float(value) for value in values)
                    except ValueError as exc:
                        raise ValueError(f"Invalid altitude in {file_path}") from exc
                    break
            else:
                raise ValueError(f"Altitude header not found in {file_path}")
    return sorted(heights)

heights_wls71 = get_heights_from_sta_files(all_sta_files_wls71)
heights_wls73 = get_heights_from_sta_files(all_sta_files_wls73)

print("Configured heights above ground (m) for WLS71460 lidar:", heights_wls71)
print("Configured heights above ground (m) for WLS73514 lidar:", heights_wls73)

####################################################################################
# Plot available wind-speed measurements at their actual timestamps and heights.
fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True, sharey=True)
for ax, data, lidar, color in [
    (axes[0], availability_wls71, 'WLS71460', 'blue'),
    (axes[1], availability_wls73, 'WLS73514', 'red'),
]:
    available = data.loc[data[lidar]]
    ax.scatter(available['Timestamp'], available['Height_m'], color=color, s=1, rasterized=True)
    ax.set_title(lidar)
    ax.set_ylabel('Height above ground (m)')
    ax.set_yticks(sorted(set(heights_wls71) | set(heights_wls73)))
    ax.set_ylim(30, 410)
    ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.4)
axes[-1].xaxis.set_major_locator(mdates.AutoDateLocator())
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d', tz='UTC'))
axes[-1].set_xlabel('Measurement date (UTC)')
fig.suptitle('Available Wind-Speed Measurements by Height')
fig.autofmt_xdate()
plt.tight_layout()
plt.show()
################################################################
# Find timestamps where both lidars have wind-speed data at all three heights.
required_heights = [40, 60, 80]
matching_measurements = measurement_availability.loc[
    measurement_availability['Height_m'].isin(required_heights)
    & measurement_availability['WLS71460'].eq(True)
    & measurement_availability['WLS73514'].eq(True)
]
matching_heights = matching_measurements.groupby('Timestamp')['Height_m'].nunique()
common_timestamps = matching_heights[matching_heights == len(required_heights)].index.sort_values()

# Print results in a readable format with both date and time
# print("\n" + "="*70)
# print("Timestamps with wind-speed data for both lidars at 40, 60, and 80 m:")
# print("="*70)
# for timestamp in common_timestamps:
#     print(f"  {timestamp.strftime('%Y-%m-%d %H:%M')}")
# print("="*70)
print(f"Total common timestamps: {len(common_timestamps)}\n")
print("First common timestamp:")
if not common_timestamps.empty:
    print(f"  {common_timestamps[0].strftime('%Y-%m-%d %H:%M %Z')}")
else:
    print("  None")

print("Last common timestamp:")
if not common_timestamps.empty:
    print(f"  {common_timestamps[-1].strftime('%Y-%m-%d %H:%M %Z')}")
else:
    print("  None")

##

######################################################################
# now with our common time range between both lidars at the required heights,
#we can make a linear regression plot for the measured wind speeds for the total common timestamps
# at the heights of 50 m (linearlly interpolated between the 40 and 60 m measurements) and 80 m
# plot the linear regression results for wind speeds at 50 m and 80 m for both lidars
# Extract wind-speed measurements for the common timestamps and required heights
# for the time range of Febuary 16 to May 24
start_date = pd.Timestamp('2026-02-16', tz='UTC')
end_date = pd.Timestamp('2026-05-24', tz='UTC')
end_exclusive = end_date + pd.Timedelta(days=1)
regression_timestamps = common_timestamps[
    (common_timestamps >= start_date) & (common_timestamps < end_exclusive)
]

def speeds_by_timestamp(availability):
    measurements = availability.loc[
        availability['Timestamp'].isin(regression_timestamps)
        & availability['Height_m'].isin(required_heights)
    ]
    return measurements.pivot(index='Timestamp', columns='Height_m', values='WindSpeed')

wls71_speeds = speeds_by_timestamp(availability_wls71)
wls73_speeds = speeds_by_timestamp(availability_wls73)
if regression_timestamps.empty:
    raise ValueError("No common measurements at 40, 60 and 80 m in the requested date range")

# Linearly interpolate 50 m, then pair both lidars on the measurement timestamp.
wls71_speeds[50] = (wls71_speeds[40] + wls71_speeds[60]) / 2
wls73_speeds[50] = (wls73_speeds[40] + wls73_speeds[60]) / 2
paired_speeds = wls71_speeds[[50, 80]].join(
    wls73_speeds[[50, 80]], how='inner', lsuffix='_wls71', rsuffix='_wls73',
)

################################################################################
# Create a time series plot for the wind speeds at 50 m and 80 m for both lidars 
# Insert missing values where successive paired measurements are more than 10 minutes apart.
gaps = paired_speeds.index.to_series().diff() > pd.Timedelta(minutes=10)
gap_times = paired_speeds.index[gaps] - pd.Timedelta(minutes=10)
plot_speeds = paired_speeds.reindex(paired_speeds.index.union(gap_times))

fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True, constrained_layout=True)
for i, height in enumerate([50, 80]):
    ax[i].plot(plot_speeds.index, plot_speeds[f'{height}_wls71'], label='WLS71', alpha=0.7)
    ax[i].plot(plot_speeds.index, plot_speeds[f'{height}_wls73'], label='WLS73', alpha=0.7)
    ax[i].set_title(f'Wind Speeds at {height} m')
    ax[i].set_ylabel('Wind Speed [m/s]')
    ax[i].legend()
    ax[i].grid(True, linestyle='--', alpha=0.7)
ax[-1].set_xlabel('Timestamp (UTC)')
fig.suptitle('Time Series of Wind Speeds at 50 m and 80 m for Both Lidars (Feb 16 to May 24, 2026 UTC)')
plt.show()


###################################################################################
# The linear regression between the wind speeds measured by WLS71 and WLS73 at 50 m and 80 m for the common timestamps
fig, ax = plt.subplots(1, 2, figsize=(12, 6), sharex=True, sharey=True, constrained_layout=True)
# Plot linear regression for wind speeds at 50 m and 80 m for both lidars
axes = ax.ravel()
heights = [50, 80]
for i, height in enumerate(heights):
    x = paired_speeds[f'{height}_wls71']
    y = paired_speeds[f'{height}_wls73']
    if len(x) < 2 or x.nunique() < 2:
        raise ValueError(f"Regression at {height} m needs at least two distinct WLS71460 wind speeds")
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    ax = axes[i]
    ax.scatter(x, y, alpha=0.7, label=f'Height {height} m')
    fit_x = np.array([x.min(), x.max()])
    ax.plot(
        fit_x, intercept + slope * fit_x, 'r',
        label=f'Fit: y={slope:.2f}x+{intercept:.2f}\nR² = {r_value**2:.2f}\nN = {len(x)}',
    )
    ax.set_title(f'Height {height} m')
    ax.set_xlabel('WLS71 Wind Speed [m/s]')
    ax.set_ylabel('WLS73 Wind Speed [m/s]')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
fig.suptitle('Linear Regression of Wind Speeds at 50 m and 80 m for Both Lidars (Feb 16 to May 24, 2026 UTC)')
plt.show()

##################################################################################
# Pull the M2 data from Feb to May 2026
dp_m2 ="C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_1min_FEB_MAY_2026_DataPull.xlsx"


#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)

print("Number of raw data points:", len(ds_m2))

# Convert fixed MST (UTC-7) to timezone-aware UTC.
mst_time = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)']).astype(str) + ' ' + ds_m2['MST'].astype(str)
ds_m2['UTC'] = (
    pd.to_datetime(mst_time, errors='raise')
    .dt.tz_localize(timezone(timedelta(hours=-7)))
    .dt.tz_convert('UTC')
)
if ds_m2['UTC'].isna().any():
    raise ValueError("Missing M2 measurement timestamp")
# Set the UTC column as the index for easier time-based operations
ds_m2.set_index('UTC', inplace=True)
ds_m2.sort_index(inplace=True)

# Include the filter to remove "flat values"
MIN_FLAT_RUN = 3 # consecutive identical samples treated as flat; adjust to the M2 sampling interval

def mask_flat_runs(series, min_run=MIN_FLAT_RUN):
    run_id = (
        (series != series.shift())
        | (series.index.to_series().diff() != pd.Timedelta(minutes=1))
    ).cumsum()
    run_len = series.groupby(run_id).transform('size')
    return series.mask((run_len >= min_run) & series.notna())

wind_columns = ["Avg Wind Speed @ 50m [m/s]", "Avg Wind Speed @ 80m [m/s]"]
missing_columns = [col for col in wind_columns if col not in ds_m2.columns]
if missing_columns:
    raise ValueError(f"Missing M2 wind speed columns: {missing_columns}")
ds_m2_filtered = ds_m2[wind_columns].copy()
for col in wind_columns:
    ds_m2_filtered[col] = pd.to_numeric(ds_m2_filtered[col], errors='raise')
    ds_m2_filtered[col] = ds_m2_filtered[col].where(ds_m2_filtered[col].between(0, 50))

if ds_m2_filtered.index.has_duplicates:
    grouped = ds_m2_filtered.groupby(level=0)
    conflicts = grouped.nunique().gt(1).any(axis=1)
    if conflicts.any():
        raise ValueError(f"Conflicting M2 measurements at {conflicts[conflicts].index[0]}")
    duplicate_count = ds_m2_filtered.index.duplicated().sum()
    warnings.warn(f"Combining {duplicate_count} duplicate M2 timestamps", stacklevel=1)
    ds_m2_filtered = grouped.first()

for col in wind_columns:
    ds_m2_filtered[col] = mask_flat_runs(ds_m2_filtered[col])

# Label each [start, end) interval with its end time in UTC.
ds_m2_filtered = (
    ds_m2_filtered.resample('10min', label='right', closed='left')
    .mean()
    .reset_index()
)

print("M2 dataset successfully flat-run filtered and resampled to 10-minute intervals.")
print("First few rows of the processed M2 dataset:")
print(ds_m2_filtered.head())

#############################################################################
#Create a time series plot for the M2 wind speed along the lidar wind speed time series perviously made
#make sure the M2 and lidar datasets have the same time index for plotting
ds_m2_filtered.set_index('UTC', inplace=True)
ds_m2_filtered.sort_index(inplace=True)

fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True, constrained_layout=True)
for i, height in enumerate([50, 80]):
    ax[i].plot(ds_m2_filtered.index, ds_m2_filtered[f'Avg Wind Speed @ {height}m [m/s]'], label='M2', alpha=0.3, linestyle='--', linewidth=0.7, color='purple')
    ax[i].plot(plot_speeds.index, plot_speeds[f'{height}_wls71'], label='WLS71', alpha=0.7)
    ax[i].plot(plot_speeds.index, plot_speeds[f'{height}_wls73'], label='WLS73', alpha=0.7)
    ax[i].set_title(f'Wind Speeds at {height} m')
    ax[i].set_ylabel('Wind Speed [m/s]')
    ax[i].legend()
    ax[i].grid(True, linestyle='--', alpha=0.7)
ax[-1].set_xlabel('Timestamp (UTC)')
fig.suptitle('Time Series of Wind Speeds at 50 m and 80 m for Both Lidars and M2(10min resampled) (Feb 16 to May 24, 2026 UTC)')
plt.show()

##############################################################################################

