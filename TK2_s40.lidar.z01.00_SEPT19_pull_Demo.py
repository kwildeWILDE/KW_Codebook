#import necessary libraries
import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Ellipse
import scipy.stats as stats
# from scipy.stats import multivariate_normal
import pandas as pd
from matplotlib.patches import Patch
import xarray as xr

#Pulling the data from the directory
dp = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair" 
file_path = f"{dp}/s40.lidar.z01.00/order_352c2b5bebd0487eaa3d59342"

def parse_hpl_file(path):
    """Parse a single Halo Photonics .hpl file into an xarray Dataset (dims: time, range)."""
    with open(path, 'r') as f:
        lines = f.readlines()

    header = {}
    for line in lines[:20]:
        if line.startswith('Number of gates:'):
            header['num_gates'] = int(line.split(':', 1)[1].strip())
        elif line.startswith('Range gate length (m):'):
            header['gate_length'] = float(line.split(':', 1)[1].strip())
        elif line.startswith('Start time:'):
            header['start_time'] = line.split(':', 1)[1].strip()

    num_gates = header['num_gates']
    # the per-ray data begins right after the "**** Instrument spectral width" line
    data_start = next(i for i, line in enumerate(lines) if line.startswith('****')) + 1

    decimal_time, azimuth, elevation, pitch, roll = [], [], [], [], []
    doppler, intensity, beta, spec_width = [], [], [], []

    i = data_start
    while i < len(lines):
        ray_header = lines[i].split()
        if len(ray_header) < 5:
            i += 1
            continue
        decimal_time.append(float(ray_header[0]))
        azimuth.append(float(ray_header[1]))
        elevation.append(float(ray_header[2]))
        pitch.append(float(ray_header[3]))
        roll.append(float(ray_header[4]))

        gate_doppler = np.full(num_gates, np.nan)
        gate_intensity = np.full(num_gates, np.nan)
        gate_beta = np.full(num_gates, np.nan)
        gate_spec = np.full(num_gates, np.nan)

        for _ in range(num_gates):
            i += 1
            vals = lines[i].split()
            gate_idx = int(vals[0])
            gate_doppler[gate_idx] = float(vals[1])
            gate_intensity[gate_idx] = float(vals[2])
            gate_beta[gate_idx] = float(vals[3])
            gate_spec[gate_idx] = float(vals[4])

        doppler.append(gate_doppler)
        intensity.append(gate_intensity)
        beta.append(gate_beta)
        spec_width.append(gate_spec)
        i += 1

    # decimal hours from the file's "Start time" date give absolute timestamps
    base_date = pd.to_datetime(header['start_time'].split()[0], format='%Y%m%d')
    time = base_date + pd.to_timedelta(decimal_time, unit='h')
    range_m = (np.arange(num_gates) + 0.5) * header['gate_length']

    return xr.Dataset(
        data_vars=dict(
            azimuth=('time', np.array(azimuth)),
            elevation=('time', np.array(elevation)),
            pitch=('time', np.array(pitch)),
            roll=('time', np.array(roll)),
            doppler_velocity=(('time', 'range'), np.array(doppler)),
            intensity=(('time', 'range'), np.array(intensity)),
            beta=(('time', 'range'), np.array(beta)),
            spectral_width=(('time', 'range'), np.array(spec_width)),
        ),
        coords=dict(time=time, range=range_m),
    )

#create one xarray dataset from the .hpl files in the order file 
hpl_files = sorted([f for f in os.listdir(file_path) if f.endswith('.hpl')])
ds = xr.concat([parse_hpl_file(f"{file_path}/{f}") for f in hpl_files], dim='time')

#read files into the xarray dataset 'ds'
print(ds.head())

# from the xarray the colomum of 'doppler_velocity' is what can be uses as the measured wind speed from the LOS lidar remote sensing method 
#but the first question is what is the height range of the measurements? 
#I'm assuminig that the values for 'range' is in meters in height away from the lidar
#With that for it to becomparable with the M2 data we can just the range heights of 15, 45, and 75 meters. 
# print(ds['range'].values)
# The 'range' coordinate represents the height above the lidar instrument at which each gate measurement is taken.
#also print the time to see if it covers the expected measurement period, as in from 00:00 SEPT 19 to 23:59 SEPT 19
#Good new that the time is around the expected measurement period
print('#########################') 
print(ds['time'].values)

# attempt to plot the doppler velocity at the specified range heights

#Convert MST into an apporite data format for plotting
desired_time = ds['time'].values[(ds['time'].values >= np.datetime64('2026-09-19T00:00:00')) & (ds['time'].values <= np.datetime64('2026-09-20T00:00:00'))]

range_heights = [15, 45, 75]
colors = ['b', 'g', 'r']

fig, ax = plt.subplots(len(range_heights), 1, figsize=(12, 4*len(range_heights)), sharex=True)

for i, h in enumerate(range_heights):
    gate_idx = np.argmin(np.abs(ds['range'].values - h))
    ax[i].plot(desired_time, ds['doppler_velocity'].values[np.isin(ds['time'].values, desired_time), gate_idx], label=f'{h} m', color=colors[i])
    ax[i].set_title(f'Doppler Velocity at {h} m')
    ax[i].set_ylabel('Doppler Velocity (m/s)')
    ax[i].legend()

#only the bottom subplot needs the time axis formatting and label since the x-axis is shared
ax[-1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
ax[-1].set_xlabel('Time')
plt.setp(ax[-1].get_xticklabels(), rotation=45, ha='right')

plt.tight_layout()
plt.show()