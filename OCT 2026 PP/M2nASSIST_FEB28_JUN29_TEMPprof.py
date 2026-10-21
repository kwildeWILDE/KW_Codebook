#import necessary libraries
from webbrowser import get

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min
import os
import glob 
from windrose import WindroseAxes
import re
#####################################################

#Pull the M2 data from the directory
#Note that this data only contains the temperature varaibles (and the data quality flags)

dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
files_m2 = f'{dp_m2}/M2_TEMPonly_FEB28_JUN29_Datapull.xlsx'

#Read the M2 files
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = files_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(files_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(files_m2)
    ds_m2.to_pickle(cache_m2)

# print (ds_m2.head())
 #convert the MST into UTC datetime
#MST is only a time of day, so combine it with the date column first
date_str = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)']).dt.strftime('%Y-%m-%d')
ds_m2['MST'] = pd.to_datetime(date_str + ' ' + ds_m2['MST'].astype(str))
ds_m2['UTC'] = ds_m2['MST'] + pd.Timedelta(hours=7)
print("MST converted to UTC successfully")

print(ds_m2['UTC'])