#import necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde, norm
import os
import glob 
import re


########### PULLING THE M2 DATA #####
dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_pub_Jan31_Present_Datapull.xlsx"

#read the file 
ds_m2 = pd.read_excel(file_path_m2)
print(ds_m2.head())

##### Convert to UTC ### 
## Jan 31 to March 8 2026 is -6 UTC 
## While March 9 2026 onwards is -7 UTC 
ds_m2['DS_time'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + ds_m2['MST'].astype(str))
ds_m2['UTC_time'] = ds_m2['DS_time'] - pd.to_timedelta(np.where(ds_m2['DATE (MM/DD/YYYY)'] < '2026-03-09', 6, 7), unit='h')

print("M2 data loaded and converted to UTC.", 
      ds_m2['UTC_time'].astype(str) )

####### Getting data quality mesh for the M2 dataset 
status_code = ds_m2['EFM Status Code'] 
# try to create a mask for good quality code 
#that skips the poor quality data (EFM Status Code > 10)
good_quality_mask = ds_m2['EFM Status Code'] <= 10
ds_m2 = ds_m2.loc[good_quality_mask]

###########################################
# For the M2 data, make a time seriers plot 
# of wind speed over time with the heights of 10, 50, 80m
#for the dates Feb 1 to present (October 14, 2026)
# Have it split up into subplots for each month

desired_dates = (ds_m2['UTC_time'] >= '2026-02-01') & (ds_m2['UTC_time'] <= '2026-10-14')
ds_m2_filtered = ds_m2.loc[desired_dates]

m2_heights = [10, 50, 80]

months = ds_m2_filtered['UTC_time'].dt.month.unique()
for month in months:
    plt.figure(figsize=(12, 6))
    ds_m2_month = ds_m2_filtered.loc[ds_m2_filtered['UTC_time'].dt.month == month]
    for height in m2_heights:
        plt.plot(ds_m2_month['UTC_time'].loc[ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'] > 0], ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'].loc[ds_m2_month[f'Avg Wind Speed @ {height}m [m/s]'] > 0], label=f'{height}m')
    plt.xlabel('UTC Time')
    plt.ylabel('Wind Speed (m/s)')
    plt.title(f'M2 Wind Speed at Different Heights (Month: {month}, 2026)')
    plt.legend()
    plt.tight_layout()
    plt.grid(True, alpha=0.3, ls='--')
    plt.show()