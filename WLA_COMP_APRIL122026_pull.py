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

# fig, ax = plt.subplots(figsize=(14, 7))
# for h, c in zip(M2_h_no_80, M2_c_no_80):
#     ax.plot(time[day], M2_series[h][day], color=c, lw=1.5, label=f"M2 {h} m")

# for h, c in zip(at_h, at_c):
#     idx = np.abs(height_m - h).argmin()
#     ax.plot(time_mst, temp_good.values[:, idx], color=c, lw=1.5, ls='--', label=f"s40.assist.tropoe {h} m")

# ax.set_xlim(np.datetime64("2026-04-12T00:00"), np.datetime64("2026-04-13T00:00"))
# ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
# ax.set_xlabel("Time (MST)")
# ax.set_ylabel("Temperature (°C)")
# ax.set_title("Temperature Time Series for April 12, 2026 (MST) without 80m M2 data")
# ax.grid(True, linestyle='--', alpha=0.4)
# ax.legend(ncol=3, fontsize=9)
# fig.tight_layout()
# plt.show()


###############################################################################
#make a (valid) temperature frequency hisogram with a KDE line for the M2 2m and 50m data 
#and the valid s40.assist.tropoe data
def clean(a):
    a = np.asarray(a, dtype=float)
    return a[~np.isnan(a)]

m2_data = [clean(M2_series[h][day]) for h in M2_h_no_80]
at_data = [clean(temp_good.values[:, np.abs(height_m - h).argmin()]) for h in at_h]

# shared bins/grid so both datasets are directly comparable
all_t = np.concatenate(m2_data + at_data)
bins = np.linspace(all_t.min(), all_t.max(), 25)
x = np.linspace(all_t.min(), all_t.max(), 500)

# fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True, sharey=True)
# panels = [
#     (axes[0], "M2", M2_h_no_80, m2_data, M2_c_no_80),
#     (axes[1], "s40.assist.tropoe (quality-masked)", at_h, at_data, at_c),
# ]
# for ax, name, heights, datasets, cols in panels:
#     for h, d, c in zip(heights, datasets, cols):
#         ax.hist(d, bins=bins, density=True, color=c, alpha=0.25)
#         ax.plot(x, gaussian_kde(d)(x), color=c, lw=2, label=f"{h} m (n={d.size})")
#     ax.set_title(name)
#     ax.set_xlabel("Temperature (°C)")
#     ax.grid(True, linestyle='--', alpha=0.4)
#     ax.legend(title="Height", fontsize=9)
# axes[0].set_ylabel("Density")
# fig.suptitle("Temperature Distribution with KDE, April 12, 2026 (MST)")
# fig.tight_layout()
# plt.show()

#################################################################################

# Make a temperature profile over height with the assist.tropoe data at 6:30 MST for April 12, 2026
time_idx = np.abs(time_mst - np.datetime64("2026-04-12T06:30")).argmin()
temp_profile = temp_good.values[time_idx, :]

# fig, ax = plt.subplots(figsize=(8, 11.5))
# ax.plot(temp_profile, height_m, marker='o', linestyle='-')
# ax.set_xlabel("Temperature (°C)")
# ax.set_ylabel("Height (m)")
# ax.set_title("s40.assist.tropoe.z01.c0 Temperature Profile at 6:30 MST, April 12, 2026")
# ax.grid(True, linestyle='--', alpha=0.4)
# fig.tight_layout()
# plt.show()
####################################################
####################################################
###################################################

################ WIND ANALYSIS SECTION ################ 

######## PULLING DATA FROM THE S40.LIDAR.Z01.C1 ############

dp_z01 = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z01.c1/order_e7b809590267433291bc26e24"

#collect every NetCDF file in the directory, in order
nc_files_z01 = sorted(glob.glob(f"{dp_z01}/*.nc"))
if not nc_files_z01:
    raise FileNotFoundError(f"No NetCDF files found in directory: {dp_z01}")

#each file has a time cordinate, so combine them directly along it. 
ds_z01 = xr.open_mfdataset(nc_files_z01, combine='by_coords').sortby("time")

########## PULLING DATA FROM THE S40.LIDAR.Z02.C0 ############

dp_z02 = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z02.c0/order_98bff4ba10b94fe2b046a64f3"

#collect every NetCDF file in the directory, in order
nc_files_z02 = sorted(glob.glob(f"{dp_z02}/*.nc"))
if not nc_files_z02:
    raise FileNotFoundError(f"No NetCDF files found in directory: {dp_z02}")

#each file has a time cordinate, so combine them directly along it. 
ds_z02 = xr.open_mfdataset(nc_files_z02, combine='by_coords').sortby("time")

###########################################################################################
#With the datasets from the M2, ds_z01 and ds_z02, we can now proceed with wind analysis.

# Align the datasets along the time coordinate
#for April 12, 2026 00:00 MST to April 12, 2026 23:59 MST
#however the time in datasets z01 and z02 are in UTC while M2 is in MST, so we need to convert the z01 and z02 times to MST
#MST is a fixed UTC-7 (no daylight saving). xarray times are tz-naive UTC, so shift them by -7 h
#and keep everything tz-naive MST so the three datasets share the same time axis.

# Convert df_m2 to a datetime index if it's not already
df_m2['time'] = pd.to_datetime(df_m2['datetime'])
df_m2.set_index('time', inplace=True)

def utc_to_mst(ds):
	ds = ds.assign_coords(time=ds["time"].to_index() - pd.Timedelta(hours=7))
	return ds.sortby("time")

ds_z01_mst = utc_to_mst(ds_z01)
ds_z02_mst = utc_to_mst(ds_z02)

# Restrict to April 12, 2026 (MST)
day_start, day_end = pd.Timestamp("2026-04-12 00:00"), pd.Timestamp("2026-04-12 23:59:59")
df_m2 = df_m2.loc[day_start:day_end]
ds_z01_mst = ds_z01_mst.sel(time=slice(day_start, day_end))
ds_z02_mst = ds_z02_mst.sel(time=slice(day_start, day_end))

# Interpolate the lidar data onto the M2 timestamps (NaN outside each lidar's coverage)
ds_z01_interp = ds_z01_mst.interp(time=df_m2.index)
ds_z02_interp = ds_z02_mst.interp(time=df_m2.index)

#print the times 
print("M2 times (MST):", df_m2.index)
print("S40.LIDAR.Z01.C1 times (MST):", ds_z01_interp.time.values)
print("S40.LIDAR.Z02.C0 times (MST):", ds_z02_interp.time.values)

##########################################################################################
#Now note that the three datasets (M2, Z01, Z02) are all aligned in time (MST) and can be compared directly.


# Heights that have at least one valid (non-NaN) wind speed on April 12 (MST) for ds_z01
valid_counts_z01 = ds_z01_interp["WS"].notnull().sum("time").compute()
valid_heights_z01 = valid_counts_z01.where(valid_counts_z01 > 0, drop=True)
print(f"Heights with valid wind speed for Z01 ({valid_heights_z01.size} of {ds_z01_interp.sizes['height']}):")
print("Lowest valid height:", int(valid_heights_z01["height"].min()), "m | Highest:", int(valid_heights_z01["height"].max()), "m")
print(pd.DataFrame({"height_m": valid_heights_z01["height"].values, "valid_samples": valid_heights_z01.values.astype(int)}).to_string(index=False))

# Heights that have at least one valid (non-NaN) wind speed on April 12 (MST) for ds_z02
valid_counts_z02 = ds_z02_interp["wind_speed"].notnull().sum("time").compute()
valid_heights_z02 = valid_counts_z02.where(valid_counts_z02 > 0, drop=True)
print(f"Heights with valid wind speed for Z02 ({valid_heights_z02.size} of {ds_z02_interp.sizes['distance']}):")
print("Lowest valid height:", int(valid_heights_z02["distance"].min()), "m | Highest:", int(valid_heights_z02["distance"].max()), "m")
print(pd.DataFrame({"height_m": valid_heights_z02["distance"].values, "valid_samples": valid_heights_z02.values.astype(int)}).to_string(index=False))





#However, the dataset have valid data at differnt heights , so select the desired heights for each of the datasets
dh_m2 = [2, 50, 80] #in meters 
dh_z01 = [120,160,200] #in meters  
dh_z02 =  [40,60,80]  #in meters

colors = ['b', 'g', 'r']

#Now that we have matching times and desiered heits for the datasets, we can try to make time seriers comparisons of the wind data. 

#Make a time seriers of the wind speed at the desired heigts for each respective dataset in their own subplots 
# but same time axis to see the agreement
import matplotlib.pyplot as plt

# fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# # M2 wind speed at desired heights
# for h in dh_m2:
# 	axes[0].plot(df_m2.index, df_m2[f"Avg Wind Speed @ {h}m [m/s]"], label=f"{h} m", color=colors[dh_m2.index(h)])
# axes[0].set_title("M2 Wind Speed at Desired Heights April 12, 2026")
# axes[0].set_ylabel("Wind Speed (m/s)")
# axes[0].legend()
# axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z01 wind speed at desired heights
# for h in dh_z01:
# 	axes[1].plot(ds_z01_interp.time.values, ds_z01_interp[f"WS"].sel(height=h), label=f"{h} m", color=colors[dh_z01.index(h)])
# axes[1].set_title("S40.LIDAR.Z01.C1 Wind Speed at Desired Heights April 12, 2026")
# axes[1].set_ylabel("Wind Speed (m/s)")
# axes[1].legend()
# axes[1].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind speed at desired heights
# for h in dh_z02:
# 	axes[2].plot(ds_z02_interp.time.values, ds_z02_interp[f"wind_speed"].sel(distance=h), label=f"{h} m", color=colors[dh_z02.index(h)])
# axes[2].set_title("S40.LIDAR.Z02.C0 Wind Speed at Desired Heights April 12, 2026")
# axes[2].set_ylabel("Wind Speed (m/s)")
# axes[2].set_xlabel("Time (MST)")
# axes[2].legend()
# axes[2].grid(True, which='both', linestyle='--', linewidth=0.5)

# plt.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()

####################################
# Do the same time sereies analysis for wind direction for each respective dataset in their own subplots 
# but same time axis to see the agreement
# fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
# # M2 wind direction at desired heights
# for h in dh_m2:
# 	axes[0].plot(df_m2.index, df_m2[f"Avg Wind Direction @ {h}m [deg]"], label=f"{h} m", color=colors[dh_m2.index(h)])
# axes[0].set_title("M2 Wind Direction at Desired Heights April 12, 2026")
# axes[0].set_ylabel("Wind Direction (deg)")
# axes[0].legend()
# axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z01 wind direction at desired heights
# for h in dh_z01:
# 	axes[1].plot(ds_z01_interp.time.values, ds_z01_interp[f"WD"].sel(height=h), label=f"{h} m", color=colors[dh_z01.index(h)])
# axes[1].set_title("S40.LIDAR.Z01.C1 Wind Direction at Desired Heights April 12, 2026")
# axes[1].set_ylabel("Wind Direction (deg)")
# axes[1].legend()
# axes[1].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind direction at desired heights
# for h in dh_z02:
# 	axes[2].plot(ds_z02_interp.time.values, ds_z02_interp[f"wind_direction"].sel(distance=h), label=f"{h} m", color=colors[dh_z02.index(h)])
# axes[2].set_title("S40.LIDAR.Z02.C0 Wind Direction at Desired Heights April 12, 2026")
# axes[2].set_ylabel("Wind Direction (deg)")
# axes[2].set_xlabel("Time (MST)")
# axes[2].legend()
# axes[2].grid(True, which='both', linestyle='--', linewidth=0.5)

# plt.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()
############################################################################## 
# Make a frequency hitogram and KDE pdf line for the wind speeds between the datasets M2, Z01, and Z02
# on the same plot for comparison

# fig, (ax_m2, ax_z01, ax_z02) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# # M2 wind speed histogram and KDE
# ax = ax_m2
# for h in dh_m2:
# 	wind_sp = np.asarray(df_m2[f"Avg Wind Speed @ {h}m [m/s]"]).ravel()
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]
# 	ax.hist(wind_sp, bins=30, density=True, label=f"M2 {h} m (n = {wind_sp.size})", color=colors[dh_m2.index(h)],alpha =0.6, histtype="step")
# 	## KDE pdf line for m2
# 	# #distribution pdf line for the wind speeds
# 	#distribution pdf line for the wind speeds
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	#KDE follows the distribution of the wind speeds
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_m2.index(h)])
# ax_m2.set_title("M2 Wind Speed Distribution April 12, 2026")
# ax_m2.set_ylabel("Density")
# ax_m2.legend()
# ax_m2.grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z01 wind speed histogram and KDE
# ax = ax_z01
# for h in dh_z01:
# 	wind_sp = np.asarray(ds_z01_interp[f"WS"].sel(height=h)).ravel()
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]
# 	ax.hist(wind_sp, bins=30, density=True, label=f"Z01 {h} m (n = {wind_sp.size})", color=colors[dh_z01.index(h)], alpha=0.6, histtype="step")
# 	## KDE pdf line for Z01
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_z01.index(h)])
# ax_z01.set_title("S40.LIDAR.Z01.C1 Wind Speed Distribution April 12, 2026")
# ax_z01.set_ylabel("Density")
# ax_z01.legend()
# ax_z01.grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind speed histogram and KDE
# ax = ax_z02
# for h in dh_z02:
# 	wind_sp = np.asarray(ds_z02_interp[f"wind_speed"].sel(distance=h)).ravel()
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]
# 	ax.hist(wind_sp, bins=30, density=True, label=f"Z02 {h} m (n = {wind_sp.size})", color=colors[dh_z02.index(h)], alpha=0.6, histtype="step")
# 	## KDE pdf line for Z02
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_z02.index(h)])
# ax_z02.set_title("S40.LIDAR.Z02.C0 Wind Speed Distribution April 12, 2026")
# ax_z02.set_ylabel("Density")
# ax_z02.set_xlabel("Wind Speed (m/s)")
# ax_z02.legend()
# ax_z02.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()

##############################################################################
#make the same histogram and KDE plots for the wind directions between the datasets M2, Z01, and Z02
#on the same plot for comparison
# fig, (ax_m2, ax_z01, ax_z02) = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# # M2 wind direction histogram and KDE
# ax = ax_m2
# for h in dh_m2:
# 	wind_sp = np.asarray(df_m2[f"Avg Wind Direction @ {h}m [deg]"]).ravel()
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]
# 	ax.hist(wind_sp, bins=30, density=True, label=f"M2 {h} m (n = {wind_sp.size})", color=colors[dh_m2.index(h)],alpha =0.6, histtype="step")
# 	## KDE pdf line for m2
# 	# #distribution pdf line for the wind directions
# 	#distribution pdf line for the wind directions
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	#KDE follows the distribution of the wind speeds
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_m2.index(h)])
# ax_m2.set_title("M2 Wind Direction Distribution April 12, 2026")
# ax_m2.set_ylabel("Density")
# ax_m2.legend()
# ax_m2.grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z01 wind direction histogram and KDE
# ax = ax_z01
# for h in dh_z01:
# 	wind_sp = np.asarray(ds_z01_interp[f"WD"].sel(height=h)).ravel()
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]
# 	ax.hist(wind_sp, bins=30, density=True, label=f"Z01 {h} m (n = {wind_sp.size})", color=colors[dh_z01.index(h)], alpha=0.6, histtype="step")
# 	## KDE pdf line for Z01
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_z01.index(h)])
# ax_z01.set_title("S40.LIDAR.Z01.C1 Wind Direction Distribution April 12, 2026")
# ax_z01.set_ylabel("Density")
# ax_z01.legend()
# ax_z01.grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind direction histogram and KDE
# ax = ax_z02
# for h in dh_z02:
# 	wind_sp = np.asarray(ds_z02_interp[f"wind_direction"].sel(distance=h)).ravel()
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]
# 	ax.hist(wind_sp, bins=30, density=True, label=f"Z02 {h} m (n = {wind_sp.size})", color=colors[dh_z02.index(h)], alpha=0.6, histtype="step")
# 	## KDE pdf line for Z02
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_z02.index(h)])
# ax_z02.set_title("S40.LIDAR.Z02.C0 Wind Direction Distribution April 12, 2026")
# ax_z02.set_ylabel("Density")
# ax_z02.set_xlabel("Wind Direction (deg)")
# ax_z02.legend()
# ax_z02.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()

#########################################################
#from the wind speed time series and ditribution make a list of high wind speed events ( over two times the standard deviation)
## and record the speed and the time in MST of the high wind speed events
#from the datasets of M2, Z01, and Z02 combined 
#as an index vertical list for high wind speed events across M2, Z01, and Z02

def find_high_wind_speed_events(df_m2, ds_z01_interp, ds_z02_interp, dh_m2, dh_z01, dh_z02):
	high_wind_events = []
	# M2 high wind speed events
	for h in dh_m2:
		wind_sp = np.asarray(df_m2[f"Avg Wind Speed @ {h}m [m/s]"]).ravel()
		valid_indices = np.flatnonzero(np.isfinite(wind_sp))
		valid_wind_sp = wind_sp[valid_indices]
		threshold = 2 * np.std(valid_wind_sp)
		high_indices = valid_indices[valid_wind_sp > threshold]
		for idx in high_indices:
			high_wind_events.append(("M2", h, wind_sp[idx], df_m2.index[idx]))
	# Z01 high wind speed events
	for h in dh_z01:
		wind_sp = np.asarray(ds_z01_interp[f"WS"].sel(height=h)).ravel()
		valid_indices = np.flatnonzero(np.isfinite(wind_sp))
		valid_wind_sp = wind_sp[valid_indices]
		threshold = 2 * np.std(valid_wind_sp)
		high_indices = valid_indices[valid_wind_sp > threshold]
		for idx in high_indices:
			high_wind_events.append(("Z01", h, wind_sp[idx], ds_z01_interp.time[idx].values))
	# Z02 high wind speed events
	for h in dh_z02:
		wind_sp = np.asarray(ds_z02_interp[f"wind_speed"].sel(distance=h)).ravel()
		valid_indices = np.flatnonzero(np.isfinite(wind_sp))
		valid_wind_sp = wind_sp[valid_indices]
		threshold = 2 * np.std(valid_wind_sp)
		high_indices = valid_indices[valid_wind_sp > threshold]
		for idx in high_indices:
			high_wind_events.append(("Z02", h, wind_sp[idx], ds_z02_interp.time[idx].values))
	return sorted(high_wind_events, key=lambda event: event[2], reverse=True)[:10]

top_wind_events = find_high_wind_speed_events(
	df_m2, ds_z01_interp, ds_z02_interp, dh_m2, dh_z01, dh_z02
)
print("Top 10 high wind speed events:")
for source, height, wind_speed, event_time in top_wind_events:
	print(f"{source} at {height} m: {wind_speed:.2f} m/s at {event_time} MST")

####################################################################################################
#Now that we have the top wind speed event happening at 21:13 MST for April 12, 2026
## We can now re analyze to correlating temperature profile from the assist.tropoe dataset at the time of the top wind speed event
## and at hegiths 0 - 200 m 
time_idx = np.abs(time_mst - np.datetime64("2026-04-12T21:21")).argmin()
# height_to_analyze = [0, 200, 10] #0 to 200 m with 10 m intervals
temp_profile = temp_good.values[time_idx, :]

fig, ax = plt.subplots(figsize=(8, 11.5))
ax.plot(temp_profile, height_m[:temp_profile.size], marker='o', linestyle='-')
ax.set_xlabel("Temperature (°C)")
ax.set_ylabel("Height (m)")
ax.set_title("s40.assist.tropoe.z01.c0 Temperature Profile at 21:21 MST, April 12, 2026")
ax.grid(True, linestyle='--', alpha=0.4)
fig.tight_layout()
plt.show()
##########################################################################################
## Now make a field map of the high wind speed time from the DDOPPLER

##################### PULLING DATA FROM THE FC.DDOPPLER DATASET ##########################

dp_dop = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/fc.ddoppler.z01.c1/order_ef1285cd9be74679b1fdb5a5d"

# Create one xarray dataset from all NetCDF files in the order.
nc_files_dop = sorted(glob.glob(f"{dp_dop}/*.nc"))
if not nc_files_dop:
	raise FileNotFoundError(f"No NetCDF files found in {dp_dop}")

# These files store timestamps in global attributes reather than coordiants. 
ds_dop = []
for nc_file in nc_files_dop:
	file_ds = xr.open_dataset(nc_file)
	start_time = np.datetime64(file_ds.attrs["start_time"])
	if start_time is None:
		file_ds.close()
		raise ValueError(f"Start time not found in {nc_file}")
	ds_dop.append(file_ds.expand_dims(time=[start_time]))

ds_dop = xr.concat(
	ds_dop, 
	dim="time",
	data_vars="all",
	coords="minimal",
	compact="override",
	combine_attrs="override",
).sortby("time")

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files_dop))
print("Variables:", list(ds_dop.data_vars))
print("Dimensions:", dict(ds_dop.sizes))
print("Max Wind Speed:", ds_dop["WS"].max().values)
print("Min Wind Speed:", ds_dop["WS"].min().values)  # Print wind speed values for verification   
	