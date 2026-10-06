    ########### GOAL: COMPARE THE WIND CHARACTERISTIC BETWEEN THE M2, S40.LIDAR.Z01.C1 AND THE S40.LIDAR.Z02.C0 DATASETS ON MAY 2, 2026 (MST)
#import the libararies
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde

# Pull up the datasets for M2, S40.LIDAR.Z01.C1, and S40.LIDAR.Z02.C0 on May 2, 2026 (MST)
#The M2 Dataset 
dp_m2 = "C:/Users/kwilde/Documents" 
file_path_m2 = f"{dp_m2}/M2_MAY022026_Datapull.xlsx"

#reading to make sure it reads right
df_m2 = pd.read_excel(file_path_m2)
print(df_m2.head())

#Convert MST into an apporite data format for plotting
df_m2['datetime'] = pd.to_datetime(df_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df_m2['MST'].astype(str))
time = df_m2['datetime']

#The S40.LIDAR.Z01.C1 Dataset
#Note taht this data set only has about 6 hours worth of data on May 2, 2026 (MST)
dp_z01 = Path('C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z01.c1/')

# Collect every NetCDF file in the directory, in order.
nc_files_z01 = sorted(dp_z01.glob("*.nc"))
if not nc_files_z01:
	raise FileNotFoundError(f"No NetCDF files found in {dp_z01}")

# Each file already has a 'time' coordinate, so combine them directly along it.
ds_z01 = xr.open_mfdataset(nc_files_z01, combine="by_coords").sortby("time")

#The S40.LIDAR.Z02.C0 Dataset
dp_z02 = Path('C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z02.c0/order_66dfced42a2b4e869f38ab35f')

# Collect every NetCDF file in the directory, in order.
nc_files_z02 = sorted(dp_z02.glob("*.nc"))
if not nc_files_z02:
	raise FileNotFoundError(f"No NetCDF files found in {dp_z02}")

# Each file already has a 'time' coordinate, so combine them directly along it.
ds_z02 = xr.open_mfdataset(nc_files_z02, combine="by_coords").sortby("time")

#####################################################################################
# Now we have the three datasets loaded: df_m2, ds_z01, and ds_z02
# Next steps could involve aligning them in time, extracting wind characteristics, and comparing them.

# Example: Align the datasets in time
# Convert df_m2 to a datetime index if it's not already
df_m2['time'] = pd.to_datetime(df_m2['datetime'])
df_m2.set_index('time', inplace=True)

# Resample or interpolate the lidar datasets to match the M2 timestamps if needed
#however the time in datasets z01 and z02 are in UTC while M2 is in MST, so we need to convert the z01 and z02 times to MST
#MST is a fixed UTC-7 (no daylight saving). xarray times are tz-naive UTC, so shift them by -7 h
#and keep everything tz-naive MST so the three datasets share the same time axis.
def utc_to_mst(ds):
	ds = ds.assign_coords(time=ds["time"].to_index() - pd.Timedelta(hours=7))
	return ds.sortby("time")

ds_z01_mst = utc_to_mst(ds_z01)
ds_z02_mst = utc_to_mst(ds_z02)

# Restrict to May 2, 2026 (MST)
day_start, day_end = pd.Timestamp("2026-05-02 00:00"), pd.Timestamp("2026-05-02 23:59:59")
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

#############################
#Now note that the three datasets (M2, Z01, Z02) are all aligned in time (MST) and can be compared directly.
#However, the dataset have valid data at differnt heights , so select the desired heights for each of the datasets
dh_m2 = [2, 50, 80] #in meters 
dh_z01 = [260,300,340] #in meters  
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
# axes[0].set_title("M2 Wind Speed at Desired Heights May 02, 2026")
# axes[0].set_ylabel("Wind Speed (m/s)")
# axes[0].legend()
# axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z01 wind speed at desired heights
# for h in dh_z01:
# 	axes[1].plot(ds_z01_interp.time.values, ds_z01_interp[f"WS"].sel(height=h), label=f"{h} m", color=colors[dh_z01.index(h)])
# axes[1].set_title("S40.LIDAR.Z01.C1 Wind Speed at Desired Heights May 02, 2026")
# axes[1].set_ylabel("Wind Speed (m/s)")
# axes[1].legend()
# axes[1].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind speed at desired heights
# for h in dh_z02:
# 	axes[2].plot(ds_z02_interp.time.values, ds_z02_interp[f"wind_speed"].sel(distance=h), label=f"{h} m", color=colors[dh_z02.index(h)])
# axes[2].set_title("S40.LIDAR.Z02.C0 Wind Speed at Desired Heights May 02, 2026")
# axes[2].set_ylabel("Wind Speed (m/s)")
# axes[2].set_xlabel("Time (MST)")
# axes[2].legend()
# axes[2].grid(True, which='both', linestyle='--', linewidth=0.5)

# plt.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()

#########################################################
#DO the same time series comparison for the wind direction at the desired heights for each respective dataset in their own subplots 
# but same time axis to see the agreement
# fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
# # M2 wind direction at desired heights
# for h in dh_m2:
# 	axes[0].plot(df_m2.index, df_m2[f"Avg Wind Direction @ {h}m [deg]"], label=f"{h} m", color=colors[dh_m2.index(h)])
# axes[0].set_title("M2 Wind Direction at Desired Heights May 02, 2026")
# axes[0].set_ylabel("Wind Direction (deg)")
# axes[0].legend()
# axes[0].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z01 wind direction at desired heights
# for h in dh_z01:
# 	axes[1].plot(ds_z01_interp.time.values, ds_z01_interp[f"WD"].sel(height=h), label=f"{h} m", color=colors[dh_z01.index(h)])
# axes[1].set_title("S40.LIDAR.Z01.C1 Wind Direction at Desired Heights May 02, 2026")
# axes[1].set_ylabel("Wind Direction (deg)")
# axes[1].legend()
# axes[1].grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind direction at desired heights
# for h in dh_z02:
# 	axes[2].plot(ds_z02_interp.time.values, ds_z02_interp[f"wind_direction"].sel(distance=h), label=f"{h} m", color=colors[dh_z02.index(h)])
# axes[2].set_title("S40.LIDAR.Z02.C0 Wind Direction at Desired Heights May 02, 2026")
# axes[2].set_ylabel("Wind Direction (deg)")
# axes[2].set_xlabel("Time (MST)")
# axes[2].legend()
# axes[2].grid(True, which='both', linestyle='--', linewidth=0.5)

# plt.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()

########################################################################
#making of the histograms and the KDE odf line for the wind speed from the respective datasets
# on the same plot to see agreement
# Not considering data from s40.lidar.z01.c1 since there's only 6 hours worth of data whild M2 and Z02 have full day data

# fig, (ax_m2, ax_z02) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# # M2 wind speed histogram and KDE
# ax = ax_m2
# for h in dh_m2:
# 	ax.hist(df_m2[f"Avg Wind Speed @ {h}m [m/s]"], bins=30, density=True, label=f"M2 {h} m", color=colors[dh_m2.index(h)],alpha =0.6, histtype="step")
# 	## KDE pdf line for m2
# 	# #distribution pdf line for the wind speeds
# 	#distribution pdf line for the wind speeds
# 	wind_sp = np.asarray(df_m2[f"Avg Wind Speed @ {h}m [m/s]"]).ravel()  # convert xarray DataArray to a plain 1D numpy array
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]  # remove NaN values
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	#KDE follows the distribution of the wind speeds
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_m2.index(h)])
# ax_m2.set_title("M2 Wind Speed Distribution May 02, 2026")
# ax_m2.set_ylabel("Density")
# ax_m2.legend()
# ax_m2.grid(True, which='both', linestyle='--', linewidth=0.5)

# # Z02 wind speed histogram and KDE
# ax = ax_z02
# for h in dh_z02:
# 	ax.hist(ds_z02_interp[f"wind_speed"].sel(distance=h).values, bins=30, density=True, label=f"Z02 {h} m", color=colors[dh_z02.index(h)],alpha =0.6, histtype="step")
# 	## KDE pdf line for Z02
# 	wind_sp = np.asarray(ds_z02_interp[f"wind_speed"].sel(distance=h).values).ravel()  # convert xarray DataArray to a plain 1D numpy array
# 	wind_sp = wind_sp[~np.isnan(wind_sp)]  # remove NaN values
# 	sp_min = np.nanmin(wind_sp)
# 	sp_max = np.nanmax(wind_sp)
# 	#KDE follows the distribution of the wind speeds
# 	wind_sp_kde = gaussian_kde(wind_sp)
# 	x = np.linspace(sp_min, sp_max, 1000)
# 	ax.plot(x, wind_sp_kde(x), color=colors[dh_z02.index(h)])

# ax_z02.set_title("S40.LIDAR.Z02.C0 Wind Speed Distribution May 02, 2026")
# ax_z02.set_xlabel("Wind Speed (m/s)")
# ax_z02.set_ylabel("Density")
# ax_z02.legend()
# ax_z02.grid(True, which='both', linestyle='--', linewidth=0.5)
# plt.tight_layout()
# plt.show()

##################################################################################################################
#Do the same for wind direction histograms and KDE for M2 and Z02
fig, (ax_m2, ax_z02) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# M2 wind speed histogram and KDE
ax = ax_m2
for h in dh_m2:
	ax.hist(df_m2[f"Avg Wind Direction @ {h}m [deg]"], bins=30, density=True, label=f"M2 {h} m", color=colors[dh_m2.index(h)],alpha =0.6, histtype="step")
	## KDE pdf line for m2
	# #distribution pdf line for the wind directions
	#distribution pdf line for the wind directions
	wind_dir = np.asarray(df_m2[f"Avg Wind Direction @ {h}m [deg]"]).ravel()  # convert xarray DataArray to a plain 1D numpy array
	wind_dir = wind_dir[~np.isnan(wind_dir)]  # remove NaN values
	dir_min = np.nanmin(wind_dir)
	dir_max = np.nanmax(wind_dir)
	#KDE follows the distribution of the wind directions
	wind_dir_kde = gaussian_kde(wind_dir)
	x = np.linspace(dir_min, dir_max, 1000)
	ax.plot(x, wind_dir_kde(x), color=colors[dh_m2.index(h)])
ax_m2.set_title("M2 Wind Direction Distribution May 02, 2026")
ax_m2.set_ylabel("Density")
ax_m2.legend()
ax_m2.grid(True, which='both', linestyle='--', linewidth=0.5)

# Z02 wind speed histogram and KDE
ax = ax_z02
for h in dh_z02:
	ax.hist(ds_z02_interp[f"wind_direction"].sel(distance=h).values, bins=30, density=True, label=f"Z02 {h} m", color=colors[dh_z02.index(h)],alpha =0.6, histtype="step")
	## KDE pdf line for Z02
	wind_dir = np.asarray(ds_z02_interp[f"wind_direction"].sel(distance=h).values).ravel()  # convert xarray DataArray to a plain 1D numpy array
	wind_dir = wind_dir[~np.isnan(wind_dir)]  # remove NaN values
	dir_min = np.nanmin(wind_dir)
	dir_max = np.nanmax(wind_dir)
	#KDE follows the distribution of the wind directions
	wind_dir_kde = gaussian_kde(wind_dir)
	x = np.linspace(dir_min, dir_max, 1000)
	ax.plot(x, wind_dir_kde(x), color=colors[dh_z02.index(h)])

ax_z02.set_title("S40.LIDAR.Z02.C0 Wind Direction Distribution May 02, 2026")
ax_z02.set_xlabel("Wind Direction (°)")
ax_z02.set_ylabel("Density")
ax_z02.legend()
ax_z02.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()

#################################################################### 
#End of the wind analysis between the different datasets 
#Stop here because there is no data from the assist.tropoe data for May 02, 2026