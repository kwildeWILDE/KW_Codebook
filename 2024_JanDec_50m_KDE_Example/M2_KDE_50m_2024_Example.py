#import necessary libraries
from webbrowser import get

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd 
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse, Patch
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min, multivariate_normal
import os
import glob 
import re
import seaborn as sns

##################################################
#Pulling the M2 Data 
# #Data is at 50 m and goes from Jan 1, 2024 to Dec 31, 2024

dp_m2 ="C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/2024_JanDec_M2_50m_Data.xlsx"

#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)

print("Number of raw data points:", len(ds_m2))

#Convert to UTC 
#The current M2 data is in MST to UTC is +7 hours
#establish the regular datetime index to be readable
mst_time = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)']).astype(str) + ' ' + ds_m2['HOUR-MST'].astype(str) + ':00'

ds_m2['datetime'] = pd.to_datetime(mst_time)
ds_m2['datetime_utc'] = ds_m2['datetime'] + pd.Timedelta(hours=7)

#read to see if the time conversion worked correctly
# print(ds_m2[['datetime', 'datetime_utc']].head())
# Awesome 'datetime_utc" works perfectly #

#Getting thedata quality mesh for the M2 dataset
status_code = ds_m2['Avg EFM Status Code']
#make a mask for good quality code
#that skips the poor quality data (EFM Status Code > 10 )
good_quality_mask = status_code <= 10
ds_m2 = ds_m2.loc[good_quality_mask]

#read to see if the quality filtering worked correctly
# print(ds_m2[['Avg EFM Status Code']].head())
# Quality mesh works !!

# Another filter through the dataset is for it to skip over unrealisitic values like '-99999'
ds_m2 = ds_m2.replace(-99999, np.nan)

# Remove complete runs of three or more hourly readings that are flat in any variable.
flat_threshold = 3  # consecutive hourly readings
flat_tolerance = 1e-6
flat_columns = [
    'Avg Temperature @ 50m [deg C]',
    'Avg Avg Wind Speed @ 50m [m/s]',
    'Avg Turbulence Intensity @ 50m',
    'Avg Richardson Number (2-50m)',
]
before_flat_filter = len(ds_m2)
ordered_m2 = ds_m2.sort_values('datetime_utc')
consecutive_hour = ordered_m2['datetime_utc'].diff().eq(pd.Timedelta(hours=1))
flat_mask = pd.Series(False, index=ordered_m2.index)
for column in flat_columns:
    same_as_previous = ordered_m2[column].diff().abs().le(flat_tolerance) & consecutive_hour
    runs = (~same_as_previous).cumsum()
    run_length = ordered_m2[column].groupby(runs).transform('size')
    flat_mask |= ordered_m2[column].notna() & run_length.ge(flat_threshold)

ds_m2 = ds_m2.loc[~flat_mask]

print("Number of data points before flat filter:", before_flat_filter)
print("Number of data points removed by flat filter:", before_flat_filter - len(ds_m2))
print("Number of data points after flat filter:", len(ds_m2))

# At this point, the dataset has been filtered for quality and flat runs.
# create an dataset variable name that can be used for further analysis
#contains the UTC datatimes all of the data quality and flat run filters applied
ds_m2_filtered = ds_m2.copy()
print("Filtered dataset created." , ds_m2_filtered.head())
print("Number of data points in filtered dataset:", len(ds_m2_filtered))
################################################################
##[GET BACK TO AFTER FINISHING ANALYZING RAW L;IDAR DATSET]