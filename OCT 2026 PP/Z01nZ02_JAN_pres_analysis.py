#import necessary libraries
from webbrowser import get

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
import re

#pull the datasets
##PULLING THE DATA FROM THE S40.LIDAR.Z01.C1 FROM WDH #######
dp_z01 = "C:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data/corsair"
dfp_z01 = f"{dp_z01}//s40.lidar.z01.c1/order_bcf33e155d61445faecd3ae80"

#collect every NetCDF file in the directory, in order
nc_files_z01 = sorted(glob.glob(f"{dfp_z01}/*.nc"))
if not nc_files_z01:
    raise FileNotFoundError(f"No NetCDF files found in directory: {dfp_z01}")

#some files contain NaT times, which breaks by_coords' monotonic check,
#so concatenate along time, drop NaT/duplicate times, then sort.
ds_z01 = xr.open_mfdataset(nc_files_z01, combine='nested', concat_dim='time',
                           data_vars='minimal', coords='minimal', compat='override')
ds_z01 = ds_z01.isel(time=ds_z01['time'].notnull().values).sortby('time')
ds_z01 = ds_z01.isel(time=~ds_z01.get_index('time').duplicated())

print("Successfully loaded S40 LIDAR Z01 C1 data.")
print(ds_z01.head())
print('##' * 40)
z01_time = ds_z01['time']
print(z01_time)
ds_z01['datetime'] = ('time', pd.to_datetime(ds_z01['time'].astype(str).values))
print(ds_z01['datetime'])

##############################################
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

#######################################################
#make sure the time coordinates between Z01 and Z02 datasets are aligned
z02_time = ds_z02['time']
print(z02_time)
ds_z02['time'] = ('time', pd.to_datetime(ds_z02['time'].astype(str).values))
print(ds_z02['time'])

#check if the time coordinates are aligned
if not np.array_equal(ds_z01['time'].values, ds_z02['time'].values):
    print("Warning: Time coordinates between Z01 and Z02 datasets are not aligned.")
else:
    print("Time coordinates between Z01 and Z02 datasets are aligned.")

#since the output from the lines above the datasets are NOT aligned, we need to align them
common_times = np.intersect1d(ds_z01['time'].values, ds_z02['time'].values)
ds_z01 = ds_z01.sel(time=common_times)
ds_z02 = ds_z02.sel(time=common_times)

print("Datasets have been aligned to common time coordinates.")
print("Z01 dataset after alignment:")
print(ds_z01.head())
print("Z02 dataset after alignment:")
print(ds_z02.head())

print("Common time coordinates:")
print(common_times)

#####################################
## if the time coordinates were not aligned initially, we have now aligned them to common times.
# we can merge the Z01 and Z02 datasets along the time dimension
ds_merged = xr.merge([ds_z01, ds_z02], compat='override')
print("Merged dataset:")
print(ds_merged.head())
print("Merged dataset time coordinates:")
print(ds_merged['time'])

#########################
# WITH THE merged dataset, start to make a mean wind speed profiles for the diurnal cycle on a month to month basis
# group the merged dataset by month and hour to calculate the mean wind speed profiles
ds_merged['month'] = ds_merged['time'].dt.month
ds_merged['hour'] = ds_merged['time'].dt.hour
mean_wind_profiles = ds_merged.groupby(['month', 'hour']).mean(dim='time')
print("Mean wind speed profiles for the diurnal cycle on a month to month basis:")
print(mean_wind_profiles)

#Got an error fix later tomrrow
