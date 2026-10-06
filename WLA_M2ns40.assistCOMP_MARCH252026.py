#importing the libararies
import numpy as np
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde

################
#pulling the M2 data from MARCH 25, 2026

# Pull up the datasets for M2, S40.LIDAR.Z01.C1, and S40.LIDAR.Z02.C0 on May 2, 2026 (MST)
#The M2 Dataset 
dp_m2 = "C:/Users/kwilde/Documents" 
file_path_m2 = f"{dp_m2}/M2_MARCH25_2026_Datapull.xlsx"

#reading to make sure it reads right
df_m2 = pd.read_excel(file_path_m2)
print(df_m2.head())

#Convert MST into an apporite data format for plotting
df_m2['datetime'] = pd.to_datetime(df_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df_m2['MST'].astype(str))
time = df_m2['datetime']

## The M2 temperatures are varibles
M2_t_2m = df_m2["Temperature @ 2m [deg C]"]
M2_t_50m = df_m2["Temperature @ 50m [deg C]"]
M2_t_80m = df_m2["Temperature @ 80m [deg C]"]

### Pulling the S40.LIDAR.Z01.C0 data from MARCH 25, 2026 
#pulling the s40.lidar.z01.c1 dataset from the local directory
dp_at = Path('C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.assist.tropoe.z01.c0/order_f4f7a9ca00a04907bc5116523')

# Collect every NetCDF file in the directory, in order.
nc_files = sorted(dp_at.glob("*.nc"))
if not nc_files:
	raise FileNotFoundError(f"No NetCDF files found in {dp_at}")

# Each file already has a 'time' coordinate, so combine them directly along it.
ds_at = xr.open_mfdataset(nc_files, combine="by_coords", data_vars="minimal", coords="minimal", compat="override").sortby("time")

####################
#get a varible of the heigt in terms of meters
height_m = ds_at["height"].values * 1000
#get the time range fro March 25 00:00 to March 25 23:59 in MST
time_start = np.datetime64("2026-03-25T00:00:00") + np.timedelta64(7, 'h')
time_end = np.datetime64("2026-03-25T23:59:59") + np.timedelta64(7, 'h')    

ds_selected_mst = ds_at.sel(time=slice(time_start, time_end))
print("Selected Time Range (MST):", ds_selected_mst["time"].values.min() - np.timedelta64(7, 'h'), "to", ds_selected_mst["time"].values.max() - np.timedelta64(7, 'h'))

## Make print a variable of the height range in meters
height_range_m = (height_m.min(), height_m.max())
print("Height Range (in meters):", height_range_m[0], "to", height_range_m[1], "meters")

# make a list of the the heights in meters and the frequency of valid temperature data across the selected time range
valid_temp_mask = ~np.isnan(ds_selected_mst["temperature"].values)
valid_height_indices = np.any(valid_temp_mask, axis=0).nonzero()[0]
valid_heights = height_m[valid_height_indices]
height_frequency = np.sum(valid_temp_mask, axis=0)[valid_height_indices]
for h, f in zip(valid_heights, height_frequency):
    print(f"Height: {h} meters, Frequency of Valid Temperature Data: {f}")

#create a quality mask (time, height) based on the notes from WDH
# rmsa and gamma are per-time values, so broadcast them across height
rmsa_ok = (ds_selected_mst["rmsa"] <= 5)
gamma_ok = (ds_selected_mst["gamma"] <= 1)
# above cloud base is suspect when LWP > 5 g/m^2 (cbh is in km, same as height)
above_cloud = (ds_selected_mst["height"] > ds_selected_mst["cbh"]) & (ds_selected_mst["lwp"] > 5)
quality_mask = rmsa_ok & gamma_ok & ~above_cloud   # True = good data

# set bad points to NaN so the plot skips over them
temp_good = ds_selected_mst["temperature"].where(quality_mask)
time_mst = ds_selected_mst["time"].values - np.timedelta64(7, 'h')

## Reprint the list of valid heights with temperature data after applying the quality mask within the time range of March 25, 2026 (MST)
temp_good_march25 = temp_good  # already limited to March 25 MST
valid_temp_good_mask = ~np.isnan(temp_good_march25.values)
valid_height_indices_good = np.any(valid_temp_good_mask, axis=0).nonzero()[0]
valid_heights_good = height_m[valid_height_indices_good]
height_frequency_good = np.sum(valid_temp_good_mask, axis=0)[valid_height_indices_good]
for h, f in zip(valid_heights_good, height_frequency_good):
    print(f"Height: {h} meters, Frequency of Valid Temperature Data (after quality mask, March 25, 2026): {f}")

###################################################################
# Make a temperature time series plot for temperature with the data from the M2 and the valid 
# temperature data after applying the quality mask from s40.assist.tropoe for March 25, 2026 (MST)

M2_h = np.array([2, 50, 80]) #heights for the M2 temperature time series plot
M2_c = ['b' , 'g', 'r'] #colors assigned to the respective heights for the M2 temperature time series plot

at_h = np.array([0, 10, 46, 61, 77, 95]) #heights for the s40.assist.tropoe temperature time series plot
at_c = ['royalblue', 'mediumslateblue', 'springgreen', 'limegreen', 'gold', 'tomato'] #colors assigned to the respective heights 
    #for the s40.assist.tropoe temperature time series plot

# M2 series live in the dataframe (not the assist dataset); keep only March 25 MST
M2_series = {2: M2_t_2m, 50: M2_t_50m, 80: M2_t_80m}
day = (time >= "2026-03-25 00:00") & (time < "2026-03-26 00:00")

# fig, ax = plt.subplots(figsize=(14, 7))
# for h, c in zip(M2_h, M2_c):
#     ax.plot(time[day], M2_series[h][day], color=c, lw=1.5, label=f"M2 {h} m")

# for h, c in zip(at_h, at_c):
#     idx = np.abs(height_m - h).argmin()
#     ax.plot(time_mst, temp_good.values[:, idx], color=c, lw=1.5, ls='--', label=f"s40.assist.tropoe {h} m")

# ax.set_xlim(np.datetime64("2026-03-25T00:00"), np.datetime64("2026-03-26T00:00"))
# ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
# ax.set_xlabel("Time (MST)")
# ax.set_ylabel("Temperature (°C)")
# ax.set_title("Temperature Time Series for March 25, 2026 (MST)")
# ax.grid(True, linestyle='--', alpha=0.4)
# ax.legend(ncol=3, fontsize=9)
# fig.tight_layout()
# plt.show()

#################### 
#Make the same time series plot for temperature but getting rid of the 80m M2 data 
M2_h_no_80 = np.array([2, 50]) #heights for the M2 temperature time series plot without 80m
M2_c_no_80 = ['b' , 'g'] #colors assigned to the respective heights for the M2 temperature time series plot without 80m

fig, ax = plt.subplots(figsize=(14, 7))
for h, c in zip(M2_h_no_80, M2_c_no_80):
    ax.plot(time[day], M2_series[h][day], color=c, lw=1.5, label=f"M2 {h} m")

for h, c in zip(at_h, at_c):
    idx = np.abs(height_m - h).argmin()
    ax.plot(time_mst, temp_good.values[:, idx], color=c, lw=1.5, ls='--', label=f"s40.assist.tropoe {h} m")

ax.set_xlim(np.datetime64("2026-03-25T00:00"), np.datetime64("2026-03-26T00:00"))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.set_xlabel("Time (MST)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Temperature Time Series for March 25, 2026 (MST) without 80m M2 data")
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(ncol=3, fontsize=9)
fig.tight_layout()
plt.show()
