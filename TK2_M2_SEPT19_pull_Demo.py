#import libraries
import numpy as np
import pandas as pd
import xarray as xr 
import matplotlib.pyplot as plt
import os 
from pathlib import Path
import matplotlib.dates as mdates

#upload the excel file
dp = "C:/Users/kwilde/Documents" 
file_path = f"{dp}/PUB_M2_SEPT19_2026.xlsx"

#reading to make sure it reads right
df = pd.read_excel(file_path)
print(df.head())

#set up the datadrame into a xarray Dataset
ds = df.to_xarray()
print(ds.head(5))  # Display the first 5 rows of the xarray Dataset to verify conversion

##############################################################################################
#setting up the variables for plotting
temp2 = ds['Temperature @ 2m [deg C]']
temp50 = ds['Temperature @ 50m [deg C]']
temp80 = ds['Temperature @ 80m [deg C]']

#Convert MST into an apporite data format for plotting
df['datetime'] = pd.to_datetime(df['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df['MST'].astype(str))
time = df['datetime']

#####################################################################
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
# plt.title('Temperature Over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

#########################################################
#Plotting the potential temperatures over time at different heights
#potnetal tmep (theata) is the temperature a parcel of air would have if it were 
# expanded or compressed adiabatically to a standard pressure (usually 1000 hPa)

#standard pressure p*
stnd_pressure = ds['Sea-Level Pressure (Est) [mBar]']

#pressure at the station
pressure = ds['Station Pressure [mBar]']

# k-constant for dry air (k = R/cp)
k_con = 0.286  # R/cp for dry air

#potential temperature at different heights
theta2 = (temp2 + 273.15) * (stnd_pressure / pressure) ** k_con
theta50 = (temp50 + 273.15) * (stnd_pressure / pressure) ** k_con
theta80 = (temp80 + 273.15) * (stnd_pressure / pressure) ** k_con

plt.figure(figsize=(12, 6))
plt.plot(time, theta2, label='Potential Temperature @ 2m [K]', color='blue')
plt.plot(time, theta50, label='Potential Temperature @ 50m [K]', color='green')
plt.plot(time, theta80, label='Potential Temperature @ 80m [K]', color='red')

#setting up the x-axis to show time in a readable format
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

plt.xlabel('Time')
plt.ylabel('Potential Temperature [K]')
plt.title('Potential Temperature Over Time SEPT 19 2026')
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.legend(fontsize=10)
plt.show()

##############################################
#Regret Not getting the Dew Temp brb pullig that up 