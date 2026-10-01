#import libraries
import numpy as np
import pandas as pd
import xarray as xr 
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.patches import Ellipse, Patch
import os 
from pathlib import Path
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde, norm, multivariate_normal

#upload the excel file
dp = "C:/Users/kwilde/Documents" 
file_path = f"{dp}/M2_JUNE162026_Datapull.xlsx"

#reading to make sure it reads right
df = pd.read_excel(file_path)
print(df.head())

#set up the datadrame into a xarray Dataset
ds = df.to_xarray()
print(ds.head(5))  # Display the first 5 rows of the xarray Dataset to verify conversion

###############################################################################

#setting up the variables for plotting
temp2 = ds['Temperature @ 2m [deg C]']
temp50 = ds['Temperature @ 50m [deg C]']
temp80 = ds['Temperature @ 80m [deg C]']

#Convert MST into an apporite data format for plotting
df['datetime'] = pd.to_datetime(df['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df['MST'].astype(str))
time = df['datetime']
################################################################################################
#Plotting the temperatures over time at different heights 

# plt.figure(figsize=(12, 6))
# plt.plot(time, temp2, label='Temperature @ 2m [deg C]', color='blue')
# plt.plot(time, temp50, label='Temperature @ 50m [deg C]', color='green')
# plt.plot(time, temp80, label='Temperature @ 80m [deg C]', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Temperature [Deg C]')
# plt.title('Temperature Over Time JUNE 16 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

###########################################################
#Plotting the wind speeds over time at different heights 

# wind_sp2 = ds['Avg Wind Speed @ 2m [m/s]']
# wind_sp5 = ds['Avg Wind Speed @ 5m [m/s]']
# wind_sp10 = ds['Avg Wind Speed @ 10m [m/s]']
# wind_sp20 = ds['Avg Wind Speed @ 20m [m/s]']
# wind_sp50 = ds['Avg Wind Speed @ 50m [m/s]']
# wind_sp80 = ds['Avg Wind Speed @ 80m [m/s]']

# plt.figure(figsize=(12, 6))
# plt.plot(time, wind_sp2, label='Wind Speed @ 2m [m/s]', color='blue')
# plt.plot(time, wind_sp5, label='Wind Speed @ 5m [m/s]', color='cyan')
# plt.plot(time, wind_sp10, label='Wind Speed @ 10m [m/s]', color='magenta')
# plt.plot(time, wind_sp20, label='Wind Speed @ 20m [m/s]', color='yellow')
# plt.plot(time, wind_sp50, label='Wind Speed @ 50m [m/s]', color='green')
# plt.plot(time, wind_sp80, label='Wind Speed @ 80m [m/s]', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Wind Speed [m/s]')
# plt.title('Wind Speed Over Time JUNE 16 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

###############################################################
#Plotting the Wind direction over time at the different heights
wind_dir2 = ds['Avg Wind Direction @ 2m [deg]']
wind_dir5 = ds['Avg Wind Direction @ 5m [deg]']
wind_dir10 = ds['Avg Wind Direction @ 10m [deg]']
wind_dir20 = ds['Avg Wind Direction @ 20m [deg]']
wind_dir50 = ds['Avg Wind Direction @ 50m [deg]']
wind_dir80 = ds['Avg Wind Direction @ 80m [deg]']

plt.figure(figsize=(12, 6))
plt.plot(time, wind_dir2, label='Wind Direction @ 2m [deg]', color='blue')
plt.plot(time, wind_dir5, label='Wind Direction @ 5m [deg]', color='cyan')
plt.plot(time, wind_dir10, label='Wind Direction @ 10m [deg]', color='magenta')
plt.plot(time, wind_dir20, label='Wind Direction @ 20m [deg]', color='yellow')
plt.plot(time, wind_dir50, label='Wind Direction @ 50m [deg]', color='green')
plt.plot(time, wind_dir80, label='Wind Direction @ 80m [deg]', color='red')

#setting up the x-axis to show time in a readable format
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

plt.xlabel('Time')
plt.ylabel('Wind Direction [deg]')
plt.title('Wind Direction Over Time JUNE 16 2026')
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.legend(fontsize=10, loc='lower right')
plt.show()
#########################################################

