#import the libararies
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde
import glob

############# PULL THE M2 DATA #############

dp_m2 = "C:/Users/kwilde/Documents"
file_path_m2 = f"{dp_m2}/M2_APRIL122026_Datapull.xlsx"

#read the M2 file 
df_m2 = pd.read_excel(file_path_m2)
print(df_m2.head())

## Convert MST into an apporite data format 
df_m2['datetime'] = pd.to_datetime(df_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df_m2['MST'].astype(str))
time = df_m2['datetime']

### Plot the time series of the M2 Richardson Number to get an idea of possible turbulent through the day of April 12, 2026
## Setting up the varibles for the M2 Ri number for plotting 
ri_250 = df_m2['Richardson Number (2-50m)']
ri_280 = df_m2['Richardson Number (2-80m)']
ri_5080 = df_m2['Richardson Number (50-80m)']

# plt.figure(figsize=(12,6))
# plt.plot(time, ri_250,c='purple', label='Ri 2-50m')
# plt.plot(time, ri_280,c='orange', label='Ri 2-80m')
# plt.plot(time, ri_5080,c='green',alpha=0.25, label='Ri 50-80m')
# plt.axhline(0,c='r', linewidth=0.5, linestyle='--')

# ## setting up the x-axis to be more readable with hour and minute format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# #have the richardson numberplot in a log scale for smoother looking results
# plt.yscale('symlog', linthresh=0.10)

# plt.xlabel('Time')
# plt.ylabel('Richardson Number')
# plt.title('M2 Richardson Number Time Series - April 12, 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.legend(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.show()

########################################################

## PULLING DATA FROM THE S40.ASSIST.TROPOE.Z01.C0 FILE ############

dp_at =  "C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.assist.tropoe.z01.c0/order_86af2254f0d945f6b87710b6b"

#collect the .nc files from the April 12,2026 assist.tropoe file
nc_files_at = sorted(glob.glob(f"{dp_at}/*.nc"))
if not nc_files_at:
	raise FileNotFoundError(f"No NetCDF files found in {dp_at}")

# Each file already has a 'time' coordinate, so combine them directly along it.
ds_at = xr.open_mfdataset(nc_files_at, combine="by_coords", data_vars="minimal", coords="minimal", compat="override").sortby("time")

#get a varible of the heigt in terms of meters
height_m = ds_at["height"].values * 1000

#get the assist.tropoe time range for April 12, 2026 in MST from April 12 00:00 to April 12 23:59
time_start = np.datetime64("2026-04-12T00:00:00") + np.timedelta64(7, 'h')
time_end = np.datetime64("2026-04-12T23:59:59") + np.timedelta64(7, 'h')    

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
    print(f"Height: {h} meters, Frequency of Valid Temperature Data in the assist.tropoe data: {f}")

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

## Reprint the list of valid heights with temperature data after applying the quality mask within the time range of April 12, 2026 (MST)
temp_good_march25 = temp_good  # already limited to April 12 MST
valid_temp_good_mask = ~np.isnan(temp_good_march25.values)
valid_height_indices_good = np.any(valid_temp_good_mask, axis=0).nonzero()[0]
valid_heights_good = height_m[valid_height_indices_good]
height_frequency_good = np.sum(valid_temp_good_mask, axis=0)[valid_height_indices_good]
for h, f in zip(valid_heights_good, height_frequency_good):
    print(f"Height: {h} meters, Frequency of Valid Temperature Data (after quality mask, April 12, 2026): {f}")

###################################################################
#Make a temperature time series with the data from the M and the 
## valid temperature data after applying the quality mask for assist.tropoe 

#varible for temperature from the M2 data
m2_t_2m = df_m2["Temperature @ 2m [deg C]"]
m2_t_50m = df_m2["Temperature @ 50m [deg C]"]
m2_t_80m = df_m2["Temperature @ 80m [deg C]"]

M2_h = np.array([2, 50, 80]) #heights for the M2 temperature time series plot
M2_c = ['b' , 'g', 'r'] #colors assigned to the respective heights for the M2 temperature time series plot

at_h = np.array([0, 10, 46, 61, 77, 95]) #heights for the s40.assist.tropoe temperature time series plot
at_c = ['royalblue', 'mediumslateblue', 'springgreen', 'limegreen', 'gold', 'tomato'] #colors assigned to the respective heights 
    #for the s40.assist.tropoe temperature time series plot

# M2 series live in the dataframe (not the assist dataset); keep only March 25 MST
M2_series = {2: m2_t_2m, 50: m2_t_50m, 80: m2_t_80m}
day = (time >= "2026-04-12 00:00") & (time < "2026-04-13 00:00")

# fig, ax = plt.subplots(figsize=(14, 7))
# for h, c in zip(M2_h, M2_c):
#     ax.plot(time[day], M2_series[h][day], color=c, lw=1.5, label=f"M2 {h} m")

# for h, c in zip(at_h, at_c):
#     idx = np.abs(height_m - h).argmin()
#     ax.plot(time_mst, temp_good.values[:, idx], color=c, lw=1.5, ls='--', label=f"s40.assist.tropoe {h} m")

# ax.set_xlim(np.datetime64("2026-04-12T00:00"), np.datetime64("2026-04-13T00:00"))
# ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
# ax.set_xlabel("Time (MST)")
# ax.set_ylabel("Temperature (°C)")
# ax.set_title("Temperature Time Series for April 12, 2026 (MST)")
# ax.grid(True, linestyle='--', alpha=0.4)
# ax.legend(ncol=3, fontsize=9)
# fig.tight_layout()
# plt.show()

## Do  the same timeeeries plot without the the 80m M2 data

M2_h_no_80 = np.array([2, 50]) #heights for the M2 temperature time series plot without 80m
M2_c_no_80 = ['b' , 'g'] #colors assigned to the respective heights for the M2 temperature time series plot without 80m

fig, ax = plt.subplots(figsize=(14, 7))
for h, c in zip(M2_h_no_80, M2_c_no_80):
    ax.plot(time[day], M2_series[h][day], color=c, lw=1.5, label=f"M2 {h} m")

for h, c in zip(at_h, at_c):
    idx = np.abs(height_m - h).argmin()
    ax.plot(time_mst, temp_good.values[:, idx], color=c, lw=1.5, ls='--', label=f"s40.assist.tropoe {h} m")

ax.set_xlim(np.datetime64("2026-04-12T00:00"), np.datetime64("2026-04-13T00:00"))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.set_xlabel("Time (MST)")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Temperature Time Series for April 12, 2026 (MST) without 80m M2 data")
ax.grid(True, linestyle='--', alpha=0.4)
ax.legend(ncol=3, fontsize=9)
fig.tight_layout()
plt.show()
