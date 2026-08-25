#Pub_M2_pull_Demo

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
file_path = f"{dp}/PUB_M2_AUG23_24_2026.xlsx"


df = pd.read_excel(file_path)

#double check the data
print(df.head())

# Messing with the data
# set up df to an xarray dataset
ds = df.to_xarray()
print(ds.head())

#plot the tempperature over time at the different heights [deg C] ]
#REMEBER THAT RECALLING XARRAY NAMES IS CASE SENSITIVE
temp2 = ds['Temperature @ 2m [deg C]']
temp50 = ds['Temperature @ 50m [deg C]']
temp80 = ds['Temperature @ 80m [deg C]']



#Convert MSt into an apporite data format for plotting
df['datetime'] = pd.to_datetime(df['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df['MST'].astype(str))
time = df['datetime']


plt.figure(figsize=(12, 6))
plt.plot(time, temp2, label='Temperature @ 2m [deg C]', color='blue')
plt.plot(time, temp50, label='Temperature @ 50m [deg C]', color='green')
plt.plot(time, temp80, label='Temperature @ 80m [deg C]', color='red')

#setting up the x-axis to show time in a readable format
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

plt.xlabel('Time')
plt.ylabel('Temperature [Deg C]')
plt.title('Temperature Over Time ')
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.legend(fontsize=10)
#plt.show()

#Save the plot to a folder
#output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
#output_path = f"{output_folder}/AUG23_24_M2_TEMPS.png"  

# Create the folder if it doesn't exist
#os.makedirs(output_folder, exist_ok=True)

# Save the plot
#plt.savefig(output_path, dpi=300, bbox_inches='tight')
#print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#plotting the wind speeds over time at the different heights [m/s] 

avg_ws2 = ds['Avg Wind Speed @ 2m [m/s]']
avg_ws5 = ds['Avg Wind Speed @ 5m [m/s]']
avg_ws10 = ds['Avg Wind Speed @ 10m [m/s]']
avg_ws20 = ds['Avg Wind Speed @ 20m [m/s]']
avg_ws50 = ds['Avg Wind Speed @ 50m [m/s]']
avg_ws80 = ds['Avg Wind Speed @ 80m [m/s]']

plt.figure(figsize=(12, 6))
plt.plot(time, avg_ws2, label='Avg Wind Speed @ 2m [m/s]', color='blue')
plt.plot(time, avg_ws5, label='Avg Wind Speed @ 5m [m/s]', color='orange')
plt.plot(time, avg_ws10, label='Avg Wind Speed @ 10m [m/s]', color='green')
plt.plot(time, avg_ws20, label='Avg Wind Speed @ 20m [m/s]', color='red')
plt.plot(time, avg_ws50, label='Avg Wind Speed @ 50m [m/s]', color='purple')
plt.plot(time, avg_ws80, label='Avg Wind Speed @ 80m [m/s]', color='pink')

#setting up the x-axis to show time in a readable format
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

plt.xlabel('Time')
plt.ylabel('Average Wind Speed [m/s]')
plt.title('Wind Speed Over Time')
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.legend(fontsize=10)
plt.show()

#saving the wind speed plot to a folder

