#importing the libararies
import numpy as np
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde

#pulling the s40.lidar.z01.c1 dataset from the local directory
dp = Path('C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.assist.tropoe.z01.c0/order_f4f7a9ca00a04907bc5116523')

# Collect every NetCDF file in the directory, in order.
nc_files = sorted(dp.glob("*.nc"))
if not nc_files:
	raise FileNotFoundError(f"No NetCDF files found in {dp}")

# Each file already has a 'time' coordinate, so combine them directly along it.
ds = xr.open_mfdataset(nc_files, combine="by_coords", data_vars="minimal", coords="minimal", compat="override").sortby("time")


# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.sizes))
print("##" * 20)

print("Height Range:", ds["height"].values.min(), "to", ds["height"].values.max(), "kilometers")
#print in terms of meters
print("Height Range (in meters):", ds["height"].values.min() * 1000, "to", ds["height"].values.max() * 1000, "meters")
print("##" * 20)

# Optionally, you can also print the time range
print("Time Range:", ds["time"].values.min(), "to", ds["time"].values.max(), "UTC")
# convert the time range in terms of MST
print("Time Range (MST):", ds["time"].values.min() - np.timedelta64(7, 'h'), "to", ds["time"].values.max() - np.timedelta64(7, 'h'))

####################
#get a varible of the heigt in terms of meters
height_m = ds["height"].values * 1000
#get the time range fro March 25 00:00 to March 25 23:59 in MST
time_start = np.datetime64("2026-03-25T00:00:00") + np.timedelta64(7, 'h')
time_end = np.datetime64("2026-03-25T23:59:59") + np.timedelta64(7, 'h')    

#create a variable for the selected time range in MST
ds_selected_mst = ds.sel(time=slice(time_start, time_end))
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

#From the notes from WDH: 
## "Data with rmsa > 5 and gamma > 1 should be rejected.
##  Data above cloud base height if the liquid water path is greater than 5 g/m^2 are also suspect."

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



## Time series for March 25, 2026 (MST) at specific heights, respecting the quality mask
specific_heights_m = np.array([0, 10, 46, 61, 77, 95])
colors = ['royalblue', 'mediumslateblue', 'springgreen', 'limegreen', 'gold', 'tomato']

# fig, ax = plt.subplots(figsize=(12, 6))
# for h, color in zip(specific_heights_m, colors):
#     idx = np.abs(height_m - h).argmin()
#     ax.plot(time_mst, temp_good.values[:, idx], color=color, label=f"{height_m[idx]:.0f} m")
# ax.set_title("s40.assist.tropoe.z01.c0 Quality-masked Temperature, March 25, 2026 (MST)")
# ax.set_xlabel("Time (MST)")
# ax.set_xlim(np.datetime64("2026-03-25T00:00"), np.datetime64("2026-03-26T00:00"))
# ax.set_ylabel("Temperature (C)")
# ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
# ax.grid(True)
# ax.legend(title="Height")
# fig.tight_layout()
# plt.show()

#################################
# Make a histogram  with a KDE pdf line overlayed of the frequency of valid temperature data at each height for March 25, 2026 (MST)
# one panel per height, same bins/axes so the distributions match the time series above
heights_idx = [np.abs(height_m - h).argmin() for h in specific_heights_m]
data_by_height = []
for idx in heights_idx:
    d = temp_good_march25.values[:, idx]
    data_by_height.append(d[~np.isnan(d)])
all_t = np.concatenate(data_by_height)
bins = np.linspace(all_t.min(), all_t.max(), 20)
x = np.linspace(all_t.min(), all_t.max(), 500)

fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharex=True, sharey=True)
for ax, idx, data, c in zip(axes.flat, heights_idx, data_by_height, colors):
    ax.hist(data, bins=bins, density=True, color=c, alpha=0.4, edgecolor='white')
    ax.plot(x, gaussian_kde(data)(x), color=c, lw=2)
    ax.set_title(f"{height_m[idx]:.0f} m (n={data.size})", fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.4)
for ax in axes[1]:
    ax.set_xlabel("Temperature (C)")
for ax in axes[:, 0]:
    ax.set_ylabel("Density")
fig.suptitle("s40.assist.tropoe.z01.c0 Quality-masked Temperature Distribution, March 25, 2026 (MST)")
fig.tight_layout()
plt.show()

##############################################