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
# Plot file timestamps against configured measurement heights.
fig, ax = plt.subplots(figsize=(10, 6))
for i, height in enumerate(heights_wls71):
    ax.plot(times_wls71, [height]*len(times_wls71), 'bo', markersize=5,
            label='WLS71460' if i == 0 else None)
for i, height in enumerate(heights_wls73):
    ax.plot(times_wls73, [height]*len(times_wls73), 'rx', markersize=4,
            label='WLS73514' if i == 0 else None)
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.set_yticks(range(40, 401, 20))
ax.set_ylim(30, 410)
fig.autofmt_xdate()
plt.xlabel('Date')
plt.ylabel('Height above ground (m)')
plt.title('Configured Heights at File Timestamps for WLS71460 and WLS73514')
plt.legend()
plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.4)
plt.tight_layout()
plt.show()
