#import necessary libraries
from webbrowser import get


import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import numpy as np
from scipy.stats import stats 
import glob 
import os 
import re 
import scipy.stats as stats 

##############################################
# pull the dual doppler wind speed for making the wind speed profies for APRIL 
# pull the data from the directory 

dp = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data"
df = f'{dp}/corsair/fc.ddoppler.z01.c1/order_c9d0c27eec5a4cb9a447c16e4'

#create one xarra dataset from all NetCDF files in order 
nc_files = glob.glob(f'{df}/*.nc')
if not nc_files:
    raise FileNotFoundError(f"No NetCDF files found in directory {df}")

#these files store timestamps in global attributes rather than coordinates 
datasets = []
for filepath in nc_files:
	file_ds = xr.open_dataset(filepath)
	start_time = file_ds.attrs.get("start_time")
	if start_time is None:
		file_ds.close()
		raise ValueError(f"Missing start_time attribute in {filepath}")
	datasets.append(file_ds.expand_dims(time=[pd.to_datetime(start_time)]))

ds = xr.concat(datasets, dim="time").sortby("time")

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.sizes))
print("Max Wind Speed:", ds["WS"].max().values)
print("Min Wind Speed:", ds["WS"].min().values)  # Print wind speed values for verification

#getting the wind speed values and filtering out NaN values for analysis
ws_values = ds["WS"].values
valid_ws_values = ws_values[np.isfinite(ws_values)]
print("Non-NaN wind speed values:", valid_ws_values)
print("Max valid wind speed:", np.max(valid_ws_values))
print("Min valid wind speed:", np.min(valid_ws_values))

#In the mettadata sigma_WS is the standard deviation of the wind speed measurements,
## which can be used as a quality indicator. We will filter out any values that are NaN or exceed a reasonable threshold for sigma_WS.
sig_ws_values = ds["sigma_WS"].values
valid_sig_ws_values = sig_ws_values[np.isfinite(sig_ws_values)]
print("Non-NaN sigma wind speed values:", valid_sig_ws_values)


# Treat sigma_WS as a quality indicator, not as a correction to WS.
MAX_SIGMA_WS = 1.0
MAX_WIND_SPEED = np.mean(valid_ws_values) + 2 * np.std(valid_ws_values)  # Set a reasonable maximum wind speed for plotting
## ^^ The reason for using mean + 2*std is to capture the majority of the data while excluding extreme outliers (i.e. + 2 values outside the std)
##typically the 2+ std method captures about 95% of the data in a normal distribution
#  This threshold helps ensure that the plotted wind speeds are representative 
# of typical conditions rather than being dominated by rare, extreme events.
print("Maximum wind speed for plotting:", MAX_WIND_SPEED)

# Filter the wind speed values based on the quality indicator and maximum wind speed
# Mask on the full arrays so WS and sigma_WS stay aligned (NaN comparisons are False)
mask = (ds["sigma_WS"] <= MAX_SIGMA_WS) & (ds["WS"] <= MAX_WIND_SPEED)
filtered_ws_values = ds["WS"].where(mask).values
filtered_ws_values = filtered_ws_values[np.isfinite(filtered_ws_values)]
# print("Filtered wind speed values:", filtered_ws_values)
# print("Max filtered wind speed:", np.max(filtered_ws_values))
# print("Min filtered wind speed:", np.min(filtered_ws_values))

#########################################################
# Summary of filtered wind speed values
print("Number of valid wind speed values:", len(valid_ws_values))
print("Number of filtered wind speed values:", len(filtered_ws_values))
print("Percentage of data retained after filtering:", 100 * len(filtered_ws_values) / len(valid_ws_values))

##################################################################
# from additonal analysis we know the date and time for the extreme wind speed events 
#with the group of the extreme outliers we can create a wind speed profile for that excat time IN APRIL 

# APRIL group of extreme event times 
## APRIL 23 07:00 UTC
## APRIL 23 14:00 UTC
## APRIL 23 15:00 UTC
## APRIL 23 16:00 UTC
## APRIL 23 17:00 UTC

#print the head of the datasee to see how the time varaible is presented
# print(ds.head())
# print(ds["time"].head())  # Check how the time variable is presented
#adjust the time format to make it easier for plotting and analysis
ds["time"] = pd.to_datetime(ds["time"].values)
# duplicate timestamps make .sel(method="nearest") fail, so keep the first of each
dup_count = int(ds.indexes["time"].duplicated().sum())
print("Duplicate timestamps:", dup_count)
ds = ds.isel(time=~ds.indexes["time"].duplicated())
print(ds["time"].head())  # Verify the time conversion

# Filter the dataset for the extreme event times in April
extreme_event_times = [
    "2026-04-23 07:00:00",
    "2026-04-23 14:00:00",
    "2026-04-23 15:00:00",
    "2026-04-23 16:00:00",
    "2026-04-23 17:00:00"
]
extreme_event_times = pd.to_datetime(extreme_event_times)
extreme_events_ds = ds.sel(time=extreme_event_times, method="nearest")
print(extreme_events_ds)

# Verify each requested time against the matched timestamp in the dataset
for requested, matched in zip(extreme_event_times, extreme_events_ds["time"].values):
    print(f"requested {requested} -> matched {pd.Timestamp(matched)}")

#####
#With tthe time of the extreme events known, we can now create wind speed profiles plots for those specific times in April
for time in extreme_event_times:
    # WS is (x, y, z) per scan; average over the horizontal domain to get a vertical profile
    profile = ds.sel(time=time, method="nearest")["WS"].mean(dim=["x", "y"], skipna=True)
    plt.figure()
    plt.plot(profile, profile["z"])
    plt.xlabel("Wind Speed (m/s)")
    plt.ylabel("Height (m)")
    # print the actual time from the dataset on the title for refrence
    actual_time = ds.sel(time=time, method="nearest")["time"].values
    plt.title(f"Wind Speed Profile at {pd.Timestamp(actual_time)}")
    plt.grid(True)
    plt.show()