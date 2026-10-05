#importing the libararies
import numpy as np
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

#pulling the s40.lidar.z01.c1 dataset from the local directory
dp = Path('C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z01.c1')

# Collect every NetCDF file in the directory, in order.
nc_files = sorted(dp.glob("*.nc"))
if not nc_files:
	raise FileNotFoundError(f"No NetCDF files found in {dp}")

# Each file already has a 'time' coordinate, so combine them directly along it.
ds = xr.open_mfdataset(nc_files, combine="by_coords").sortby("time")

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.sizes))
print("Max Wind Speed:", float(ds["WS"].max()))
print("Min Wind Speed:", float(ds["WS"].min()))

print("Height Range:", ds["height"].values.min(), "to", ds["height"].values.max(), "meters")
print('###' * 70)
print("Time Range (IN UTC):", ds["time"].values.min(), "to", ds["time"].values.max(), "IN UTC, +7 HOURS AHEAD OF MST")
print("Time Range (IN MST):", ds["time"].values.min() - np.timedelta64(7, 'h'), "to", ds["time"].values.max() - np.timedelta64(7, 'h'))
# Here is issues one when it comes to comparing this dataset with the M2 dataset is that this dataset only covers about the first 6 hours
## of the day that is recorded in the M2 dataset.

####################################################
#convert the time in the dataset from UTC to MST (UTC-7) and use MST as the time coordinate
ds = ds.assign_coords(time=ds["time"] - np.timedelta64(7, 'h'))

# keep only May 2nd in MST (the file starts on the evening of May 1st MST)
ds = ds.sel(time=slice("2026-05-02 00:00", "2026-05-02 23:59:59"))
print("Time Range (MST, May 2 only):", ds["time"].values.min(), "to", ds["time"].values.max())
#######################################################

# Heights that have at least one valid (non-NaN) wind speed on May 2 (MST)
valid_counts = ds["WS"].notnull().sum("time").compute()
valid_heights = valid_counts.where(valid_counts > 0, drop=True)
print(f"Heights with valid wind speed ({valid_heights.size} of {ds.sizes['height']}):")
print("Lowest valid height:", int(valid_heights["height"].min()), "m | Highest:", int(valid_heights["height"].max()), "m")
print(pd.DataFrame({"height_m": valid_heights["height"].values, "valid_samples": valid_heights.values.astype(int)}).to_string(index=False))

desire_h = [260,300,340]
#The reason why theses heights were choses is because they have the most valid wind speed measurements on May 2 (MST) 
ds_sel = ds.sel(height=desire_h, method="nearest")  # lidar heights are on a 20 m grid, so 2 m -> 0 m and 50 m -> 60 m
colors = ['b', 'g', 'r']  # Assign a color to each selected height

print("Selected Heights:", ds_sel["height"].values)

# Plot the MST time series of wind speed for each selected height
# fig, ax = plt.subplots(figsize=(12, 6))
# for h, c in zip(ds_sel["height"].values, colors):
#     ax.plot(ds_sel["time"].values, ds_sel["WS"].sel(height=h).values, label=f"Height {h} m", color=c)
# ax.set_xlabel("Time (MST), May 2 2026")
# ax.set_ylabel("Wind Speed (m/s)")
# ax.set_title("Wind Speed Time Series at Selected Heights (MST)")
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
# ax.grid(True, linestyle='--', alpha=0.5)
# ax.legend()
# plt.tight_layout()
# plt.show()

##########################################################################################################
# Do the same analysis for wind direction (WD)
valid_counts_wd = ds["WD"].notnull().sum("time").compute()
valid_heights_wd = valid_counts_wd.where(valid_counts_wd > 0, drop=True)
print(f"Heights with valid wind direction ({valid_heights_wd.size} of {ds.sizes['height']}):")
print("Lowest valid height:", int(valid_heights_wd["height"].min()), "m | Highest:", int(valid_heights_wd["height"].max()), "m")
print(pd.DataFrame({"height_m": valid_heights_wd["height"].values, "valid_samples": valid_heights_wd.values.astype(int)}).to_string(index=False))

desire_h_wd = [260,300,340]
ds_sel_wd = ds.sel(height=desire_h_wd, method="nearest")  # lidar heights are on a 20 m grid, so 2 m -> 0 m and 50 m -> 60 m
colors_wd = ['b', 'g', 'r']  # Assign a color to each selected height

print("Selected Heights for Wind Direction:", ds_sel_wd["height"].values)

# Plot the MST time series of wind direction for each selected height
# fig, ax = plt.subplots(figsize=(12, 6))
# for h, c in zip(ds_sel_wd["height"].values, colors_wd):
#     ax.plot(ds_sel_wd["time"].values, ds_sel_wd["WD"].sel(height=h).values, label=f"Height {h} m", color=c)
# ax.set_xlabel("Time (MST), May 2 2026")
# ax.set_ylabel("Wind Direction (degrees)")
# ax.set_title("Wind Direction Time Series at Selected Heights (MST)")
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
# ax.grid(True, linestyle='--', alpha=0.5)
# ax.legend()
# plt.tight_layout()
# plt.show()

###################################### 
# SIKE make the histogram of the frequencies of wind speed with the fitted KDE pdf line for the difffernt heights

from scipy.stats import gaussian_kde

# All heights on one axes: shared bin edges, semi-transparent bars so overlapping bins stay visible
# fig, ax = plt.subplots(figsize=(12, 6))
# ws_by_height = {h: ds_sel["WS"].sel(height=h).values for h in ds_sel["height"].values}
# ws_by_height = {h: d[~np.isnan(d)] for h, d in ws_by_height.items()}
# all_ws = np.concatenate(list(ws_by_height.values()))
# bins = np.linspace(all_ws.min(), all_ws.max(), 15)
# x = np.linspace(all_ws.min(), all_ws.max(), 1000)

# for (h, data), c in zip(ws_by_height.items(), colors):
#     ax.hist(data, bins=bins, density=True, color=c, alpha=0.3, edgecolor=c, label=f"{h} m (n={data.size})")
#     ax.plot(x, gaussian_kde(data)(x), color=c, lw=2)

# ax.set_xlabel("Wind Speed (m/s)")
# ax.set_ylabel("Frequency Density")
# ax.set_title(" s40.lidar.z01.c1 Wind Speed Distribution with KDE at Selected Heights MAY 02, 2026(MST)")
# ax.grid(True, linestyle='--', alpha=0.5)
# ax.legend(title="Height")
# plt.tight_layout()
# plt.show()

#############################
#make the same histogram for wind direction (WD)
fig, ax = plt.subplots(figsize=(12, 6))
wd_by_height = {h: ds_sel_wd["WD"].sel(height=h).values for h in ds_sel_wd["height"].values}
wd_by_height = {h: d[~np.isnan(d)] for h, d in wd_by_height.items()}
all_wd = np.concatenate(list(wd_by_height.values()))
bins = np.linspace(all_wd.min(), all_wd.max(), 15)
x = np.linspace(all_wd.min(), all_wd.max(), 1000)

for (h, data), c in zip(wd_by_height.items(), colors_wd):
    ax.hist(data, bins=bins, density=True, color=c, alpha=0.3, edgecolor=c, label=f"{h} m (n={data.size})")
    ax.plot(x, gaussian_kde(data)(x), color=c, lw=2)

ax.set_xlabel("Wind Direction (degrees)")
ax.set_ylabel("Frequency Density")
ax.set_title(" s40.lidar.z01.c1 Wind Direction Distribution with KDE at Selected Heights MAY 02, 2026(MST)")
ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(title="Height")
plt.tight_layout()
plt.show()

############################## 
#End of bacis  wind anylsis from the s40.lidar.z01.c1 dataset on MAY 02, 2026
# Note that this dataset has a limited temporal coverage, so the wind statistics may not be representative of longer-term conditions.