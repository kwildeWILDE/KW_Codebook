#import the libararies
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import gaussian_kde

############# PULL THE M2 DATA #############

dp_m2 = "C:/Users/kwilde/Documents"
file_path_m2 = f"{dp_m2}/M2_APRIL122026_Datapull.xlsx"

#read the M2 file 
df_m2 = pd.read_excel(file_path_m2)
print(df_m2.head())

## Convert MST into an apporite data format 
df_m2['datetime'] = pd.to_datetime(df_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + df_m2['MST'].astype(str))
time = df_m2['datetime']

### Plot the time series of the M2 Richardson Number to get an idea of possible turbulent through the day of April 12, 2026
## Setting up the varibles for the M2 Ri number for plotting 
ri_250 = df_m2['Richardson Number (2-50m)']
ri_280 = df_m2['Richardson Number (2-80m)']
ri_5080 = df_m2['Richardson Number (50-80m)']

plt.figure(figsize=(12,6))
plt.plot(time, ri_250,c='purple', label='Ri 2-50m')
plt.plot(time, ri_280,c='orange', label='Ri 2-80m')
plt.plot(time, ri_5080,c='green',alpha=0.25, label='Ri 50-80m')
plt.axhline(0,c='r', linewidth=0.5, linestyle='--')

## setting up the x-axis to be more readable with hour and minute format
plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

#have the richardson numberplot in a log scale for smoother looking results
plt.yscale('symlog', linthresh=0.10)

plt.xlabel('Time')
plt.ylabel('Richardson Number')
plt.title('M2 Richardson Number Time Series - April 12, 2026')
plt.xticks(rotation=45, fontsize=10)
plt.yticks(fontsize=10)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
