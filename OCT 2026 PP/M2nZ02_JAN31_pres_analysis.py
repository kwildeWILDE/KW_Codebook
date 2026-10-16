#import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import matplotlib.dates as mdates
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
import re


########### PULLING THE M2 DATA #####
dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_pub_Jan31_Present_Datapull.xlsx"

#read the file 
ds_m2 = pd.read_excel(file_path_m2)
# print(ds_m2.head())

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

###########################################
# For the M2 data, make a time seriers plot 
# of wind speed over time with the heights of 10, 50, 80m
#for the dates Feb 1 to present (October 14, 2026)
# Have it split up into subplots for each month

desired_dates = (ds_m2['UTC_time'] >= '2026-02-01') & (ds_m2['UTC_time'] <= '2026-10-14')
ds_m2_filtered = ds_m2.loc[desired_dates]

m2_heights = [10, 50, 80]
m2_h_colors = {10: 'blue', 50: 'green', 80: 'red'}
m2_h_alphas = {10: 0.5, 50: 0.5, 80: 0.4}

months = ds_m2_filtered['UTC_time'].dt.month.unique()
# for month in months:
#     plt.figure(figsize=(12, 6))
#     ds_m2_month = ds_m2_filtered.loc[ds_m2_filtered['UTC_time'].dt.month == month]
#     for height in m2_heights:
#         plt.plot(ds_m2_month['UTC_time'].loc[ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'] > 0], 
#                  ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'].loc[ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'] > 0],
#                    label=f'{height}m', color=m2_h_colors[height], alpha=m2_h_alphas[height]   )
#     plt.xlabel('UTC Time')
#     plt.ylabel('Wind Speed (m/s)')
#     plt.title(f'M2 Wind Speed at Different Heights (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

#############################
#Create a histogram of the frequency of wind speeds with a Weibull fit line at different heights from the M2 datasets 
# For each of the different months. 
# for month in months:
#     plt.figure(figsize=(12, 6))
#     ds_m2_month = ds_m2_filtered.loc[ds_m2_filtered['UTC_time'].dt.month == month]
#     for height in m2_heights:
#         wind_speeds = ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'].loc[ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'] > 0]
#         plt.hist(wind_speeds, bins=30, alpha=m2_h_alphas[height], color=m2_h_colors[height], label=f'{height}m', density=True)
#         # Fit a Weibull distribution
#         if len(wind_speeds) > 0:
#             shape, loc, scale = stats.weibull_min.fit(wind_speeds, floc=0)
#             x = np.linspace(wind_speeds.min(), wind_speeds.max(), 100)
#             plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color=m2_h_colors[height], alpha=1.0)
#     plt.xlabel('Wind Speed (m/s)')
#     plt.ylabel('Frequency')
#     plt.title(f'M2 Wind Speed Distribution at Different Heights (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

##############################
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


##############################################################
###PULLING THE DATA FROM THE S40.LIDAR.Z01.C1 FROM WDH #######
# dp_z01 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data/corsair"
# dfp_z01 = f"{dp_z01}//s40.lidar.z01.c1/order_bcf33e155d61445faecd3ae80"

# #collect every NetCDF file in the directory, in order
# nc_files_z01 = sorted(glob.glob(f"{dfp_z01}/*.nc"))
# if not nc_files_z01:
#     raise FileNotFoundError(f"No NetCDF files found in directory: {dfp_z01}")

# #some files contain NaT times, which breaks by_coords' monotonic check,
# #so concatenate along time, drop NaT/duplicate times, then sort.
# ds_z01 = xr.open_mfdataset(nc_files_z01, combine='nested', concat_dim='time',
#                            data_vars='minimal', coords='minimal', compat='override')
# ds_z01 = ds_z01.isel(time=ds_z01['time'].notnull().values).sortby('time')
# ds_z01 = ds_z01.isel(time=~ds_z01.get_index('time').duplicated())

# print("Successfully loaded S40 LIDAR Z01 C1 data.")

## UPLOAD THE Z01 DATA OF ON A DIFFERENT FILE TO PREVENT LONGER RUN TIMES

#######################################################
# Make sure the time coordiante form the z02 dataset and the M2 dataset are aligned.
#The Z02 is 10-minute data and the M2 is 1-minute data, so they are NOT aligned as loaded.
#Keep only the timestamps present in both. ds_m2 is a DataFrame (UTC_time is a column),
#while ds_z02 is an xarray Dataset (time is a coordinate).
ds_m2 = ds_m2.drop_duplicates(subset='UTC_time').sort_values('UTC_time')

common_time = np.intersect1d(ds_z02['time'].values, ds_m2['UTC_time'].values)
if common_time.size == 0:
    raise ValueError("No common timestamps between Z02 and M2; check the UTC conversion.")

ds_z02 = ds_z02.sel(time=common_time)
ds_m2 = ds_m2.loc[ds_m2['UTC_time'].isin(common_time)].reset_index(drop=True)

assert np.array_equal(ds_z02['time'].values, ds_m2['UTC_time'].values)

print(f"Successfully aligned Z02 and M2 datasets on {common_time.size} common UTC times "
      f"({common_time[0]} to {common_time[-1]}).")
print(ds_z02.head(10))
print(ds_m2.head(10))
##########################################
# From the M2 created a frequency histogram with witbull fit line  of wind speed at the M2 data set at 10 m 
#for each month (Feb - October )
height = 10 # in meters
ws_col = f'Avg Wind Speed @ {height}m [m/s]'
for month in sorted(months):
    ds_m2_month = ds_m2_filtered.loc[ds_m2_filtered['UTC_time'].dt.month == month]
    wind_speeds = ds_m2_month[ws_col].loc[ds_m2_month[ws_col] > 0].dropna()
    if len(wind_speeds) < 2:
        continue
    plt.figure(figsize=(12, 6))
    plt.hist(wind_speeds, bins=30, alpha=m2_h_alphas[height], color=m2_h_colors[height],
             label=f'{height}m M2 data', density=True)
    # Fit a Weibull distribution (location fixed at 0)
    shape, loc, scale = stats.weibull_min.fit(wind_speeds, floc=0)
    x = np.linspace(wind_speeds.min(), wind_speeds.max(), 200)
    plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black',
             label=f'Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
    plt.xlabel('Wind Speed (m/s)')
    plt.ylabel('Frequency (probability density)')
    plt.title(f'M2 {height} m Wind Speed Distribution (Month: {month}, 2026)')
    plt.legend()
    plt.tight_layout()
    plt.grid(True, alpha=0.2, ls='--')
    plt.show()

    ## Save the figures later.
    


