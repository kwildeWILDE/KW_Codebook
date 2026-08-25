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
#plt.show()

#saving the wind speed plot to a folder
#output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
#output_path = f"{output_folder}/AUG23_24_M2_WINDSP.png"

# Save the plot
#plt.savefig(output_path, dpi=300, bbox_inches='tight')
#print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#plotting wind direction over time at the different heights [deg]

#avg_wd2 = ds['Avg Wind Direction @ 2m [deg]']
#avg_wd5 = ds['Avg Wind Direction @ 5m [deg]']
#avg_wd10 = ds['Avg Wind Direction @ 10m [deg]']
#avg_wd20 = ds['Avg Wind Direction @ 20m [deg]']
#avg_wd50 = ds['Avg Wind Direction @ 50m [deg]']
#avg_wd80 = ds['Avg Wind Direction @ 80m [deg]']

#convert wind direction to radians for plotting
#avg_wd2_rad = np.radians(avg_wd2)
#avg_wd5_rad = np.radians(avg_wd5)
#avg_wd10_rad = np.radians(avg_wd10)
#avg_wd20_rad = np.radians(avg_wd20)
#avg_wd50_rad = np.radians(avg_wd50)
#avg_wd80_rad = np.radians(avg_wd80)

#get the heights for the wind direction plot [meters]
heights = [2, 5, 10, 20, 50, 80]

#colors for each height
colors = ['blue', 'orange', 'green', 'red', 'purple', 'pink']

#to prevent clutter
skip= 6

#associating the heights with their colors 
for heights, colors in zip(heights, colors):
    wind_dir_col =f'Avg Wind Direction @ {heights}m [deg]' #get the column name for the current height
    wind_dir_rad = np.deg2rad(df[wind_dir_col] + 180) #convert the wind direction to radians
    vector_len = 1 #fixed length for all vectors
    u = vector_len * np.sin(wind_dir_rad) #calculate the u  (east-west) component of the wind vector
    v = vector_len * np.cos(wind_dir_rad) #calculate the v (north-south) component of the wind vector

    #plot the wind directions through the quiver method 
    plt.quiver(
        df['datetime'][::skip],  # x-coordinates (time)
        np.full_like(df['datetime'][::skip], heights),  # y-coordinates (height)
        u[::skip],  # u-component (east-west) of the wind vector
        v[::skip],  # v-component (north-south) of the wind vector
        color=colors,  # color for the wind vectors
        scale=1,  # scale for the wind vectors
        width=0.003,  # width of the wind vectors
        headwidth=3,  # width of the arrowhead
        headlength=4,  # length of the arrowhead
        label=f'{heights}m',
    )

plt.xlabel('Time', fontsize=12)
plt.ylabel('Height (m)', fontsize=12)
plt.title('Wind Direction Over Time at Different Heights', fontsize=14)
plt.xticks(rotation=45, fontsize=10)
plt.yticks(heights, fontsize=10)  # Set y-ticks to the heights
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title='Height', fontsize=10)

plt.show()