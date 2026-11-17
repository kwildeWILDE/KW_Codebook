#import necessary libraries
from webbrowser import get

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
import xarray as xr
import glob
import os
import re
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
            for line in f:
                if line.startswith('Timestamp (end of interval)'):
                    header = line.rstrip('\r\n').split('\t')
                    break
            else:
                raise ValueError(f"Measurement header not found in {file_path}")

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
        speeds = data[speed_indices].apply(pd.to_numeric, errors='raise').to_numpy()
        availability = data[availability_columns].apply(pd.to_numeric, errors='raise').to_numpy()
        available = np.isfinite(speeds) & np.isfinite(availability) & (availability > 0)
        frame = pd.DataFrame(available, columns=heights)
        frame.insert(0, 'Timestamp', measurement_times)
        frames.append(frame.melt(id_vars='Timestamp', var_name='Height_m', value_name=lidar))

    result = pd.concat(frames, ignore_index=True)
    if result.duplicated(['Timestamp', 'Height_m']).any():
        raise ValueError(f"Duplicate measurement timestamp and height for {lidar}")
    return result


availability_wls71 = get_measurement_availability(all_sta_files_wls71, 'WLS71460')
availability_wls73 = get_measurement_availability(all_sta_files_wls73, 'WLS73514')
measurement_availability = availability_wls71.merge(
    availability_wls73, on=['Timestamp', 'Height_m'], how='outer',
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
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
axes[-1].set_xlabel('Measurement date')
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
print("\n" + "="*70)
print("Timestamps with wind-speed data for both lidars at 40, 60, and 80 m:")
print("="*70)
for timestamp in common_timestamps:
    print(f"  {timestamp.strftime('%Y-%m-%d %H:%M')}")
print("="*70)
print(f"Total common timestamps: {len(common_timestamps)}\n")
print("First common timestamp:")
if not common_timestamps.empty:
    print(f"  {common_timestamps[0].strftime('%Y-%m-%d %H:%M')}")
else:
    print("  None")

print("Last common timestamp:")
if not common_timestamps.empty:
    print(f"  {common_timestamps[-1].strftime('%Y-%m-%d %H:%M')}")
else:
    print("  None")
######################################################################
# now with our common time range between both lidars at the required heights,
#we can make a linear regression plot for the measured wind speeds for the total common timestamps
# at the heights of 50 m (linearlly interpolated between the 40 and 60 m measurements) and 80 m
# plot the linear regression results for wind speeds at 50 m and 80 m for both lidars
# Extract wind-speed measurements for the common timestamps and required heights
# for the time range of Febuary 16 to May 24
start_date = pd.Timestamp('2026-02-16')
end_date = pd.Timestamp('2026-05-24')


wls71_common = availability_wls71.loc[
    availability_wls71['Timestamp'].isin(common_timestamps)
    & availability_wls71['Height_m'].isin(required_heights)
]
wls73_common = availability_wls73.loc[
    availability_wls73['Timestamp'].isin(common_timestamps)
    & availability_wls73['Height_m'].isin(required_heights)
]

wls71_common = wls71_common.loc[
    (wls71_common['Timestamp'] >= start_date)
    & (wls71_common['Timestamp'] <= end_date)
]
wls73_common = wls73_common.loc[
    (wls73_common['Timestamp'] >= start_date)
    & (wls73_common['Timestamp'] <= end_date)
]

#linearly interpolate wind speeds at 50 m between 40 and 60 m measurements
wls71_40 = wls71_common[wls71_common['Height_m'] == 40]
wls71_60 = wls71_common[wls71_common['Height_m'] == 60]
wls73_40 = wls73_common[wls73_common['Height_m'] == 40]
wls73_60 = wls73_common[wls73_common['Height_m'] == 60]

wls71_50 = (wls71_40.set_index('Timestamp')['WindSpeed'] + wls71_60.set_index('Timestamp')['WindSpeed']) / 2
wls73_50 = (wls73_40.set_index('Timestamp')['WindSpeed'] + wls73_60.set_index('Timestamp')['WindSpeed']) / 2
wls71_50 = wls71_50.reset_index()
wls73_50 = wls73_50.reset_index()

# Extract wind-speed measurements at 50 m (interpolated) and 80 m
wls71_80 = wls71_common[wls71_common['Height_m'] == 80]
wls73_80 = wls73_common[wls73_common['Height_m'] == 80]

fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharex=True, sharey=True, constrained_layout=True)
# Plot linear regression for wind speeds at 50 m and 80 m for both lidars
axes = ax.ravel()
heights = [50, 80]
for i, height in enumerate(heights):
    if height == 50:
        x = wls71_50['WindSpeed']
        y = wls73_50['WindSpeed']
    elif height == 80:
        x = wls71_80['WindSpeed']
        y = wls73_80['WindSpeed']
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    ax = axes[i]
    ax.scatter(x, y, label=f'Height {height} m')
    ax.plot(x, intercept + slope * x, 'r', label=f'Fit: y={slope:.2f}x+{intercept:.2f}')
    ax.set_title(f'Height {height} m')
    ax.set_xlabel('WLS71 Wind Speed [m/s]')
    ax.set_ylabel('WLS73 Wind Speed [m/s]')
    ax.legend()
    ax.text(0.05, 0.95, f'R² = {r_value**2:.2f}', transform=ax.transAxes, verticalalignment='top')
    ax.text(0.05, 0.90, f'Slope = {slope:.2f}', transform=ax.transAxes, verticalalignment='top')
    ax.text(0.05, 0.85, f'Intercept = {intercept:.2f}', transform=ax.transAxes, verticalalignment='top')
    ax.text(0.05, 0.80, f'P-value = {p_value:.2e}', transform=ax.transAxes, verticalalignment='top')
    ax.text(0.05, 0.75, f'Std Err = {std_err:.2e}', transform=ax.transAxes, verticalalignment='top')
    ax.text(0.05, 0.70, f'N = {len(x)}', transform=ax.transAxes, verticalalignment='top')
plt.show()

### Go back to and fix later 