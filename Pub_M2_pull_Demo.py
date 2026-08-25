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


#plt.figure(figsize=(12, 6))
#plt.plot(time, temp2, label='Temperature @ 2m [deg C]', color='blue')
#plt.plot(time, temp50, label='Temperature @ 50m [deg C]', color='green')
#plt.plot(time, temp80, label='Temperature @ 80m [deg C]', color='red')

#setting up the x-axis to show time in a readable format
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#plt.xlabel('Time')
#plt.ylabel('Temperature [Deg C]')
#plt.title('Temperature Over Time ')
#plt.xticks(rotation=45, fontsize=10)
#plt.yticks(fontsize=10)
#plt.grid(True, linestyle='--', alpha=0.5)
#plt.tight_layout()
#plt.legend(fontsize=10)
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

#plt.figure(figsize=(12, 6))
#plt.plot(time, avg_ws2, label='Avg Wind Speed @ 2m [m/s]', color='blue')
#plt.plot(time, avg_ws5, label='Avg Wind Speed @ 5m [m/s]', color='orange')
#plt.plot(time, avg_ws10, label='Avg Wind Speed @ 10m [m/s]', color='green')
#plt.plot(time, avg_ws20, label='Avg Wind Speed @ 20m [m/s]', color='red')
#plt.plot(time, avg_ws50, label='Avg Wind Speed @ 50m [m/s]', color='purple')
#plt.plot(time, avg_ws80, label='Avg Wind Speed @ 80m [m/s]', color='pink')

#setting up the x-axis to show time in a readable format
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#plt.xlabel('Time')
#plt.ylabel('Average Wind Speed [m/s]')
#plt.title('Wind Speed Over Time')
#plt.xticks(rotation=45, fontsize=10)
#plt.yticks(fontsize=10)
#plt.grid(True, linestyle='--', alpha=0.5)
#plt.tight_layout()
#plt.legend(fontsize=10)
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

#get the measurement heights for the wind direction plot [meters]
heights = [2, 5, 10, 20, 50, 80]

#colors for each height
colors = ['blue', 'orange', 'green', 'red', 'purple', 'pink']

#to prevent clutter from too many arrows
skip = 12

plt.figure(figsize=(14,8))

#associate each height with its color
for height, color in zip(heights, colors):
    wind_dir_col = f'Avg Wind Direction @ {height}m [deg]'
    wind_direction_rad = np.deg2rad(df[wind_dir_col] + 180)
    u = np.sin(wind_direction_rad)
    v = np.cos(wind_direction_rad)
    plt.quiver(
        df['datetime'][::skip],
        np.full(len(df['datetime'][::skip]), height, dtype=float),
        u[::skip],
        v[::skip],
        color=color,
        angles='uv',
        scale_units='width',
        scale=35,
        width=0.0025,
        headwidth=3,
        headlength=4,
        pivot='mid',
        label=f'{height}m',
    )

plt.xlabel('Time', fontsize=10)
plt.ylabel('Measurement Height (m)', fontsize=10)
plt.title('Wind Direction Over Time at Different Heights', fontsize=10)
plt.ylim(0, 85)
plt.yticks(heights, fontsize=10)
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
plt.xticks(rotation=45, fontsize=10)
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(title='Height', fontsize=10)

plt.tight_layout()
plt.show()

#saving wind direction plot to a folder
output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
output_path = f"{output_folder}/AUG23_24_M2_WINDDIR.png"

# Save the plot
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Plot saved to: {output_path}")


#"-----------------------------------------------------------------------------------------------------------------------"#

#Compute the wind shear exponent (power law)
# Vu = Vl * (HU/HL) ^ (exp)
## Where: 
## Vu = wind speed at upper height (m/s)
## Vl = wind speed at lower height (m/s)
## HU = upper height (m)
## HL = lower height (m)
## the exponent (exp) is the wind shear exponent

### exp < 0.21 = (very-modertly unstable) 
### 0.21 < exp < 0.25 = near nuetral
### 0.25 < exp < 0.4 = moderately stable
### 0.4 < exp = very stable

# exp = log(Vu/Vl) / log(HU/HL)

xl = 0.21 #NEAR UNSTABLE VALUE
xu = 0.4 #NEAR STABLE VALUE

H1 = 2 # in meters 
H2 = 5 #in meters
H3 = 10 #in meters
H4 = 20 #in meters
H5 = 50 #in meters
H6 = 80 #in meters 

exp_12 = np.log(avg_ws5 / avg_ws2) / np.log(H2 / H1)
exp_23 = np.log(avg_ws10 / avg_ws5) / np.log(H3 / H2)
exp_34 = np.log(avg_ws20 / avg_ws10) / np.log(H4 / H3)
exp_45 = np.log(avg_ws50 / avg_ws20) / np.log(H5 / H4)
exp_56 = np.log(avg_ws80 / avg_ws50) / np.log(H6 / H5)

#plt.figure(figsize=(12, 6))

#plt.plot(time, exp_56, label='Wind Shear Exponent (50-80m)', color='blue')
#plt.plot(time, exp_45, label='Wind Shear Exponent (20-50m)', color='green')
#plt.plot(time, exp_34, label='Wind Shear Exponent (10-20m)', color='red')
#plt.plot(time, exp_23, label='Wind Shear Exponent (5-10m)', color='orange')
#plt.plot(time, exp_12, label='Wind Shear Exponent (2-5m)', color='purple')

#plt.axhline(y=xl, color='cyan', linestyle='--', label='Near Unstable Threshold (0.21)')
#plt.axhline(y=xu, color='magenta', linestyle='--', label='Near Stable Threshold (0.4)')


#setting up the x-axis to show time in a readable format
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=6))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#plt.xlabel('Time')
#plt.ylabel('Wind Shear Exponent')
#plt.title('Wind Speed Shear Exponent Over Time at Different Heights')
#plt.xticks(rotation=45, fontsize=10)
#plt.yticks(fontsize=10)
#plt.grid(True, linestyle='--', alpha=0.5)
#plt.tight_layout()
#plt.legend(fontsize=10)


#saving the wind shear exponent plot to a folder
#output_folder = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/output_plots"
#output_path = f"{output_folder}/AUG23_24_M2_WINDSHEAR_EXP.png"

# Save the plot
#plt.savefig(output_path, dpi=300, bbox_inches='tight')
#print(f"Plot saved to: {output_path}")

#"-----------------------------------------------------------------------------------------------------------------------"#

#calculating and plotting the turbulence intensity at different heights and over time. 

#TI = V_std / V_avg --> turbulence intensity is the ratio of the standard deviation of the wind speed to the average wind speed at a given height.

