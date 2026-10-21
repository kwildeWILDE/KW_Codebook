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
# print("MST converted to UTC successfully")

# print(ds_m2['UTC'])
#filter the data so that only quality data is kept along the analysis
# poor-ish data in the M2 dataset is when the EFM Status Code is >= 9
ds_m2 = ds_m2[ds_m2['EFM Status Code'] < 9]

#create a filtered M2 dataset in UTC with only quality data
ds_m2_filtered = ds_m2.copy()

#############################################################
#Pull the ASSIST data from the directory

dp_at = "c:/Users/kwilde/OneDrive - NLR/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.assist.tropoe.z01.c0"
at_files = f'{dp_at}/order_0345338a149b488b8aabb6f46'

#collect every .nc file in order of time 
nc_files = sorted(glob.glob(f'{at_files}/*.nc'))
if not nc_files:
    raise FileNotFoundError(f"No .nc files found in {at_files}")

#creatre the .nc files into a workable xarray dataset
# Each file already has a 'time' coordinate, so combine them directly along it.
ds_at = xr.open_mfdataset(nc_files, combine="by_coords", data_vars="minimal", coords="minimal", compat="override").sortby("time")

#check if the dataset has been loaded correctly
#print(ds_at.head())

#filter through the ASSIST dataset to keep only quality data
# From the WDH notes: 
## "Data with rmsa > 5 and gamma > 1 should be rejected. Data above cloud base height 
# #if the liquid water path is greater than 5 g/m^2 are also suspect."

#drop=True isn't supported on dask arrays, so bad data is masked as NaN instead
#variable names are cbh and lwp; cbh and height are both in km
ds_at_filtered = ds_at.where((ds_at['rmsa'] <= 5) & (ds_at['gamma'] <= 1))
ds_at_filtered = ds_at_filtered.where((ds_at_filtered['cbh'] <= ds_at_filtered['height']) | (ds_at_filtered['lwp'] <= 5))
print("ASSIST dataset successfully filtered")
#print(ds_at_filtered)

####################################################################################
#Now that we have the filtered M2 and ASSIST datasets, 
#We can now create the necessary plots to find the agreement in tempature from both datasets

# Main goal plot:
#create a month to month temperature over height heat map (ASSIST) with the scattered M2 temperature points overlaid
#for the height range being 0-200 (for the ASSIST)
#and the scatter points from the M2 being at heights of 2, 50, and 80m (only heights available in the dataset)

#create the varaibles for temperature at certain heights from the M2 dataset
m2_temp_2m =ds_m2_filtered["Temperature @ 2m [deg C]"]
m2_temp_50m =ds_m2_filtered["Temperature @ 50m [deg C]"]
#m2_temp_80m =ds_m2_filtered["Temperature @ 80m [deg C]"]

#create a variable for the ASSIST temperature profile from 0 to 200m
#ASSIST height is in km, so 0-200 m is 0-0.2 km
at_temp_0_200m = ds_at_filtered['temperature'].sel(height=slice(0, 0.2))

# When plotting the scatter points from the M2, dataset make sure the heights 
#have their corresponding color based on the height they represent 
#define the colors for each height
height_colors = {
    2: 'cyan',
    50: 'magenta',
}

#make sure that the time varaible between M2 and ASSIST datasets are aligned
#make sure they have the same variable for the month of the year


# Now try to make a month by month (late FEB - late JUN) temperature over height heat map (from the ASSIST dataset) 
# with M2 scatter points
import matplotlib.pyplot as plt

months = [2, 3, 4, 5, 6]  # late February to late June

#load the small 0-200m ASSIST subset into memory so boolean masks can be used (dask arrays can't be indexed by boolean dask arrays)
at_temp_0_200m = at_temp_0_200m.load()
at_months = at_temp_0_200m['time'].dt.month.values
m2_months = ds_m2_filtered['UTC'].dt.month

for month in months:
    #filter the ASSIST and M2 datasets for the current month
    print(f"Processing month: {month}")
    at_temp_0_200m_month = at_temp_0_200m.isel(time=np.where(at_months == month)[0])
    m2_month = ds_m2_filtered[m2_months == month]
    m2_temp_2m_month = m2_month.set_index('UTC')["Temperature @ 2m [deg C]"]
    m2_temp_50m_month = m2_month.set_index('UTC')["Temperature @ 50m [deg C]"]
    #m2_temp_80m_month = m2_month.set_index('UTC')["Temperature @ 80m [deg C]"]
    # print(f"ASSIST data points for month {month}: {len(at_temp_0_200m_month['time'])}")
    # print(f"M2 2m data points for month {month}: {len(m2_temp_2m_month['time'])}")
    # print(f"M2 50m data points for month {month}: {len(m2_temp_50m_month['time'])}")
    # print(f"M2 80m data points for month {month}: {len(m2_temp_80m_month['time'])}")
    #create the figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    #plot the ASSIST temperature profile as a heat map
    pcm = ax.pcolormesh(at_temp_0_200m_month['time'], at_temp_0_200m_month['height'] * 1000, at_temp_0_200m_month.T, shading='auto', cmap='viridis')
    fig.colorbar(pcm, ax=ax, label='Temperature [deg C]')

    #overlay the M2 scatter points on a second y-axis (temperature) so their variation is visible
    #make sure that the M2 scatter points only include positive temperature values or valid measurements
    ax2 = ax.twinx()
    ax2.scatter(m2_temp_2m_month.index[m2_temp_2m_month.values > -20], m2_temp_2m_month.values[m2_temp_2m_month.values > -20], c=height_colors[2], label='M2 2m', s=5,)
    ax2.scatter(m2_temp_50m_month.index[m2_temp_50m_month.values > -20], m2_temp_50m_month.values[m2_temp_50m_month.values > -20], c=height_colors[50], label='M2 50m', s=5)
    #ax2.scatter(m2_temp_80m_month.index, m2_temp_80m_month.values, c=height_colors[80], label='M2 80m', s=10)

    ax.set_ylim(0, 200)
    ax.set_xlabel('Time')
    ax.set_ylabel('Height [m] (ASSIST)')
    ax2.set_ylabel('M2 Temperature [deg C]')
    plt.title(f'Temperature over Height (ASSIST) with M2 Scatter Points for month {month}, 2026')
    ax2.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

# Note: The 80m M2 temperature data has been poorly recored there and is therefore not included in the plots.#### 
#fix later 
