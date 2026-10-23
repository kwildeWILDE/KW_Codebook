#import necessary libraries
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
from windrose import WindroseAxes
import re


########### PULLING THE M2 DATA #####
#Pull the Full M2 data from Jan 31 to Oct 17, 2026 
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

###########################################
# For the M2 data, make a time seriers plot 
# of wind speed over time with the heights of 10, 50, 80m
#for the dates Feb 1 to present (October 14, 2026)
# Have it split up into subplots for each month

desired_dates = (ds_m2['UTC_time'] >= '2026-02-01') & (ds_m2['UTC_time'] <= '2026-10-14')
ds_m2_filtered = ds_m2.loc[desired_dates]


#############################
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
ds_z02 = xr.open_mfdataset(nc_files_z02, combine='nested', concat_dim='time', parallel=True,
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
ds_m2_all = ds_m2.copy()  # unaligned M2 (Z02 ends Sep 14, so alignment drops October)
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


################################################
# Make a month by month time line of wind speed at 50m with the M2 and the z02 datasets
# get the m2 50m timelines to ignore the points is below zero or NaN
z02_h = ds_z02['distance'] 
#select the single height first, then load into memory once so each monthly plot doesn't re-read the files
z02_50m_ws = ds_z02['wind_speed'].sel(distance=50, method='nearest').load()

m2_50m_col = 'Avg Wind Speed @ 50m [m/s]'
# filter the time and the wind speed together so they keep the same length
ds_m2_50m = ds_m2.loc[ds_m2[m2_50m_col] > 0, ['UTC_time', m2_50m_col]]  # NaN fails > 0 too

m2_80m_col = 'Avg Wind Speed @ 80m [m/s]'
ds_m2_80m = ds_m2.loc[ds_m2[m2_80m_col] > 0, ['UTC_time', m2_80m_col]]  # NaN fails > 0 too

# for month in sorted(months):
#     z02_month = z02_50m_ws.sel(time=z02_50m_ws['time'].dt.month == month)
#     m2_month = ds_m2_50m.loc[ds_m2_50m['UTC_time'].dt.month == month]
#     plt.figure(figsize=(12, 6))
#     plt.plot(z02_month['time'], z02_month, label='Z02 50m Wind Speed', color='limegreen', ls='--')
#     plt.plot(m2_month['UTC_time'], m2_month[m2_50m_col], label='M2 50m Wind Speed', color='green', alpha=0.7, ls='-')
#     plt.xlabel('Time')
#     plt.ylabel('Wind Speed (m/s)')
#     plt.title(f'50m Wind Speed (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

################################################################
# Make a frequency distribution histogram and fit a Weibull distribution 
# #of wind speed at 50m for each month with the M2 and Z02 datasets

m2_all_50m = ds_m2_all.loc[ds_m2_all[m2_50m_col] > 0, ['UTC_time', m2_50m_col]]
hist_months = sorted(set(pd.DatetimeIndex(common_time).month) | set(m2_all_50m['UTC_time'].dt.month))
hist_months = sorted(set(pd.DatetimeIndex(common_time).month) | set(m2_all_50m['UTC_time'].dt.month))
hist_months = [m for m in hist_months if 2 <= m <= 9]
# for month in hist_months:
#     z02_month = z02_50m_ws.sel(time=z02_50m_ws['time'].dt.month == month)
#     # use the Z02-aligned M2 where Z02 exists; otherwise (October) use all M2 data
#     m2_src = ds_m2_50m if z02_month.size > 0 else m2_all_50m
#     m2_month = m2_src.loc[m2_src['UTC_time'].dt.month == month]
#     z02_wind_speeds = z02_month.values.flatten()
#     z02_wind_speeds = z02_wind_speeds[z02_wind_speeds > 0]
#     m2_wind_speeds = m2_month[m2_50m_col].loc[m2_month[m2_50m_col] > 0]
#     if len(z02_wind_speeds) < 2 and len(m2_wind_speeds) < 2:
#         continue
#     plt.figure(figsize=(12, 6))
#     if len(z02_wind_speeds) >= 2:
#         plt.hist(z02_wind_speeds, bins=30, alpha=0.5, color='mediumblue', label='Z02 50m Wind Speed', density=True)
#         shape, loc, scale = stats.weibull_min.fit(z02_wind_speeds, floc=0)
#         x = np.linspace(z02_wind_speeds.min(), z02_wind_speeds.max(), 200)
#         plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black', label=f'Z02 Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
#     if len(m2_wind_speeds) >= 2:
#         plt.hist(m2_wind_speeds, bins=30, alpha=0.5, color='green', label='M2 50m Wind Speed', density=True)
#         shape, loc, scale = stats.weibull_min.fit(m2_wind_speeds, floc=0)
#         x = np.linspace(m2_wind_speeds.min(), m2_wind_speeds.max(), 200)
#         plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black', linestyle='--', label=f'M2 Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
#     plt.xlabel('Wind Speed (m/s)')
#     plt.ylabel('Frequency (probability density)')
#     plt.title(f'50m Wind Speed Distribution (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show() 

########################################################################
# Make the time series of wind speed for 80 m with the M2 and Z02 datasets
m2_all_80m = ds_m2_all.loc[ds_m2_all[m2_80m_col] > 0, ['UTC_time', m2_80m_col]]
z02_80m_ws = ds_z02['wind_speed'].sel(distance=80, method='nearest').load()
# m2_80m_col = 'Avg Wind Speed @ 80m [m/s]'
ds_m2_80m = ds_m2.loc[ds_m2[m2_80m_col] > 0, ['UTC_time', m2_80m_col]]  # NaN fails > 0 too

for month in hist_months:
    z02_month = z02_80m_ws.sel(time=z02_80m_ws['time'].dt.month == month)
    # use the Z02-aligned M2 where Z02 exists; otherwise (October) use all M2 data
    m2_src = ds_m2_80m if z02_month.size > 0 else m2_all_80m
    m2_month = m2_src.loc[m2_src['UTC_time'].dt.month == month]
    z02_wind_speeds = z02_month.values.flatten()
    z02_wind_speeds = z02_wind_speeds[z02_wind_speeds > 0]
    m2_wind_speeds = m2_month[m2_80m_col].loc[m2_month[m2_80m_col] > 0]
    if len(z02_wind_speeds) < 2 and len(m2_wind_speeds) < 2:
        continue
    plt.figure(figsize=(12, 6))
    if len(z02_wind_speeds) >= 2:
        plt.hist(z02_wind_speeds, bins=30, alpha=0.5, color='mediumorchid', label='Z02 80m Wind Speed', density=True)
        shape, loc, scale = stats.weibull_min.fit(z02_wind_speeds, floc=0)
        x = np.linspace(z02_wind_speeds.min(), z02_wind_speeds.max(), 200)
        plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black', label=f'Z02 Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
    if len(m2_wind_speeds) >= 2:
        plt.hist(m2_wind_speeds, bins=30, alpha=0.5, color='red', label='M2 80m Wind Speed', density=True)
        shape, loc, scale = stats.weibull_min.fit(m2_wind_speeds, floc=0)
        x = np.linspace(m2_wind_speeds.min(), m2_wind_speeds.max(), 200)
        plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black', linestyle='--', label=f'M2 Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
    plt.xlabel('Wind Speed (m/s)')
    plt.ylabel('Frequency (probability density)')
    plt.title(f'80m Wind Speed Distribution (Month: {month}, 2026)')
    plt.legend()
    plt.tight_layout()
    plt.grid(True, alpha=0.2, ls='--')
    plt.show() 

############################################################################################################
# Make the frequency distribution and fit line of wind speed for 80 m with the M2 and Z02 datasets
# for month in sorted(months):
#     z02_month = z02_80m_ws.sel(time=z02_80m_ws['time'].dt.month == month)
#     z02_month = z02_month.where(z02_month > 0, drop=True)
#     z02_ws = z02_month.values.flatten()
#     z02_ws = z02_ws[~np.isnan(z02_ws)]
#     m2_month = ds_m2_80m.loc[ds_m2_80m['UTC_time'].dt.month == month]
#     m2_ws = m2_month[m2_80m_col].to_numpy()
#     if len(z02_ws) < 2 and len(m2_ws) < 2:
#         continue
#     plt.figure(figsize=(12, 6))
#     if len(z02_ws) >= 2:
#         plt.hist(z02_ws, bins=30, alpha=0.5, color='pink', label='Z02 80m Wind Speed', density=True)
#         shape, loc, scale = stats.weibull_min.fit(z02_ws, floc=0)
#         x = np.linspace(z02_ws.min(), z02_ws.max(), 200)
#         plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black', label=f'Z02 Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
#     if len(m2_ws) >= 2:
#         plt.hist(m2_ws, bins=30, alpha=0.5, color='red', label='M2 80m Wind Speed', density=True)
#         shape, loc, scale = stats.weibull_min.fit(m2_ws, floc=0)
#         x = np.linspace(m2_ws.min(), m2_ws.max(), 200)
#         plt.plot(x, stats.weibull_min.pdf(x, shape, loc, scale), color='black', linestyle='--', label=f'M2 Weibull fit (k={shape:.2f}, c={scale:.2f} m/s)')
#     plt.xlabel('Wind Speed (m/s)')
#     plt.ylabel('Frequency (probability density)')
#     plt.title(f'80m Wind Speed Distribution (Month: {month}, 2026)')
#     plt.legend()
#     plt.tight_layout()
#     plt.grid(True, alpha=0.2, ls='--')
#     plt.show()

   ##############################################################
   ###############################################################
   # Wind Rose Analysis

###################
#make the wind rose month to month from the M2 dataset windspeed and wind direction
m2_ws_10m = ds_m2['Avg Wind Speed @ 10m [m/s]']
m2_wd_10m = ds_m2['Avg Wind Direction @ 10m [deg]']
# for month in sorted(months):
#      m2_month = ds_m2.loc[ds_m2['UTC_time'].dt.month == month]
#      if len(m2_month) < 2:
#          continue
#      ws = m2_month['Avg Wind Speed @ 10m [m/s]'].to_numpy()
#      wd = m2_month['Avg Wind Direction @ 10m [deg]'].to_numpy()
#      valid = ~np.isnan(ws) & ~np.isnan(wd) & (ws > 0)
#      ws, wd = ws[valid], wd[valid]
#      if len(ws) < 2:
#          continue
#      fig = plt.figure(figsize=(8, 8))
#      ax = WindroseAxes.from_ax(fig=fig)
#      speed_bins = np.arange(0, np.ceil(ws.max()) + 2, 2)
#      cmap = plt.get_cmap('viridis')
#      ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white', bins=speed_bins, cmap=cmap)
#      ax.set_title(f'M2 10m Wind Rose (Month: {month}, 2026)')
#      # the windrose bars aren't a mappable, so build one that matches the speed-bin colors
#      mappable = plt.cm.ScalarMappable(norm=mcolors.BoundaryNorm(speed_bins, cmap.N), cmap=cmap)
#      fig.colorbar(mappable, ax=ax, ticks=speed_bins, shrink=0.7, pad=0.1, label='Wind Speed (m/s)')
#      plt.tight_layout() 
#      plt.show()

##############################################################
#Make the wind rose month to month for 50m with the M2 and Z02 datasets
m2_ws_50m = ds_m2['Avg Wind Speed @ 50m [m/s]']
m2_wd_50m = ds_m2['Avg Wind Direction @ 50m [deg]']
#For the M2 data only have the data not below 0[m/s] at 50m
m2_ws_50m = m2_ws_50m[m2_ws_50m > 0]


z02_h = ds_z02['distance'] 
z02_50m_ws = ds_z02['wind_speed'].sel(distance=50, method='nearest').load()
z02_50m_wd = ds_z02['wind_direction'].sel(distance=50, method='nearest').load()


# for month in sorted(months):
#      m2_month = ds_m2.loc[ds_m2['UTC_time'].dt.month == month]
#      z02_month = z02_50m_ws.sel(time=z02_50m_ws['time'].dt.month == month)
#      if len(m2_month) < 2 and z02_month.size < 2:
#          continue
#      fig = plt.figure(figsize=(8, 8))
#      ax = WindroseAxes.from_ax(fig=fig)
#      if len(m2_month) >= 2:
#          ws = m2_month['Avg Wind Speed @ 50m [m/s]'].to_numpy()
#          wd = m2_month['Avg Wind Direction @ 50m [deg]'].to_numpy()
#          valid = ~np.isnan(ws) & ~np.isnan(wd) & (ws > 0)
#          ws, wd = ws[valid], wd[valid]
#          if len(ws) >= 2:
#              speed_bins = np.arange(0, np.ceil(ws.max()) + 2, 2)
#              cmap = plt.get_cmap('viridis')
#              ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white', bins=speed_bins, cmap=cmap)
#      if z02_month.size >= 2:
#          ws = z02_month.to_numpy()
#          wd = z02_50m_wd.sel(time=z02_month['time']).to_numpy()
#          valid = ~np.isnan(ws) & ~np.isnan(wd) & (ws > 0)
#          ws, wd = ws[valid], wd[valid]
#          if len(ws) >= 2:
#              speed_bins = np.arange(0, np.ceil(ws.max()) + 2, 2)
#              cmap = plt.get_cmap('viridis')
#              ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white', bins=speed_bins, cmap=cmap)
#      ax.set_title(f'M2 and lidar.Z02 50m Wind Rose (Month: {month}, 2026)')
#      mappable = plt.cm.ScalarMappable(norm=mcolors.BoundaryNorm(speed_bins, cmap.N), cmap=cmap)
#      fig.colorbar(mappable, ax=ax, ticks=speed_bins, shrink=0.7, pad=0.1, label='Wind Speed (m/s)')
#      plt.tight_layout()
#      plt.show()
########################################
# Make a wind rose at 80m with the M2 and Z02 datasets
# m2_ws_80m = ds_m2['Avg Wind Speed @ 80m [m/s]']
# m2_wd_80m = ds_m2['Avg Wind Direction @ 80m [deg]']
# #For the M2 data only have the data not below 0[m/s] at 80m
# m2_ws_80m = m2_ws_80m[m2_ws_80m > 0]

# z02_80m_ws = ds_z02['wind_speed'].sel(distance=80, method='nearest').load()
# z02_80m_wd = ds_z02['wind_direction'].sel(distance=80, method='nearest').load()

# for month in sorted(months):
#      m2_month = ds_m2.loc[ds_m2['UTC_time'].dt.month == month]
#      z02_month = z02_80m_ws.sel(time=z02_80m_ws['time'].dt.month == month)
#      if len(m2_month) < 2 and z02_month.size < 2:
#          continue
#      fig = plt.figure(figsize=(8, 8))
#      ax = WindroseAxes.from_ax(fig=fig)
#      if len(m2_month) >= 2:
#          ws = m2_month['Avg Wind Speed @ 80m [m/s]'].to_numpy()
#          wd = m2_month['Avg Wind Direction @ 80m [deg]'].to_numpy()
#          valid = ~np.isnan(ws) & ~np.isnan(wd) & (ws > 0)
#          ws, wd = ws[valid], wd[valid]
#          if len(ws) >= 2:
#              speed_bins = np.arange(0, np.ceil(ws.max()) + 2, 2)
#              cmap = plt.get_cmap('viridis')
#              ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white', bins=speed_bins, cmap=cmap)
#      if z02_month.size >= 2:
#          ws = z02_month.to_numpy()
#          wd = z02_80m_wd.sel(time=z02_month['time']).to_numpy()
#          valid = ~np.isnan(ws) & ~np.isnan(wd) & (ws > 0)
#          ws, wd = ws[valid], wd[valid]
#          if len(ws) >= 2:
#              speed_bins = np.arange(0, np.ceil(ws.max()) + 2, 2)
#              cmap = plt.get_cmap('viridis')
#              ax.bar(wd, ws, normed=True, opening=0.8, edgecolor='white', bins=speed_bins, cmap=cmap)
#      ax.set_title(f'M2 and lidar.Z02 80m Wind Rose (Month: {month}, 2026)')
#      mappable = plt.cm.ScalarMappable(norm=mcolors.BoundaryNorm(speed_bins, cmap.N), cmap=cmap)
#      fig.colorbar(mappable, ax=ax, ticks=speed_bins, shrink=0.7, pad=0.1, label='Wind Speed (m/s)')
#      plt.tight_layout()
#      plt.show()
