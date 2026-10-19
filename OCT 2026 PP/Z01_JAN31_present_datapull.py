#import necessary libraries
from webbrowser import get

import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import matplotlib.colors as mcolors
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
import re

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
################################################################
z01_h = ds_z01['height'] 

z01_ws = ds_z01['WS']

#print a list of heights with valide wind speed data
valid_heights = z01_h.where(z01_ws.notnull(), drop=True)
print(valid_heights)

# z01_h1 = z01_h.isel(height=120, method='nearest') #in meters
#fix and work through tomorrow


