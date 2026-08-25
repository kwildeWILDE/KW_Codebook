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
output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
output_path = f"{output_folder}/AUG23_24_M2_TEMPS.png"  

# Create the folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Save the plot
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to: {output_path}")


