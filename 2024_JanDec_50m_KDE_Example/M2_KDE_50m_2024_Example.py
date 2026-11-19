#import necessary libraries
from webbrowser import get

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd 
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse, Patch
import scipy.stats as stats
from scipy.stats import gaussian_kde, norm, weibull_min, multivariate_normal
import os
import glob 
import re
import seaborn as sns

##################################################
#Pulling the M2 Data 
# #Data is at 50 m and goes from Jan 1, 2024 to Dec 31, 2024

dp_m2 ="C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/2024_JanDec_M2_50m_Data.xlsx"

#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)

print("Number of raw data points:", len(ds_m2))

#Convert to UTC 
#The current M2 data is in MST to UTC is +7 hours
#establish the regular datetime index to be readable
mst_time = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)']).astype(str) + ' ' + ds_m2['HOUR-MST'].astype(str) + ':00'

ds_m2['datetime'] = pd.to_datetime(mst_time)
ds_m2['datetime_utc'] = ds_m2['datetime'] + pd.Timedelta(hours=7)

#read to see if the time conversion worked correctly
# print(ds_m2[['datetime', 'datetime_utc']].head())
# Awesome 'datetime_utc" works perfectly #

#Getting thedata quality mesh for the M2 dataset
status_code = ds_m2['Avg EFM Status Code']
#make a mask for good quality code
#that skips the poor quality data (EFM Status Code > 10 )
good_quality_mask = status_code <= 10
ds_m2 = ds_m2.loc[good_quality_mask]

#read to see if the quality filtering worked correctly
# print(ds_m2[['Avg EFM Status Code']].head())
# Quality mesh works !!

# Another filter through the dataset is for it to skip over unrealisitic values like '-99999'
ds_m2 = ds_m2.replace(-99999, np.nan)

# Remove complete runs of three or more hourly readings that are flat in any variable.
flat_threshold = 3  # consecutive hourly readings
flat_tolerance = 1e-6
flat_columns = [
    'Avg Temperature @ 50m [deg C]',
    'Avg Avg Wind Speed @ 50m [m/s]',
    'Avg Turbulence Intensity @ 50m',
    'Avg Richardson Number (2-50m)',
]
before_flat_filter = len(ds_m2)
ordered_m2 = ds_m2.sort_values('datetime_utc')
consecutive_hour = ordered_m2['datetime_utc'].diff().eq(pd.Timedelta(hours=1))
flat_mask = pd.Series(False, index=ordered_m2.index)
for column in flat_columns:
    same_as_previous = ordered_m2[column].diff().abs().le(flat_tolerance) & consecutive_hour
    runs = (~same_as_previous).cumsum()
    run_length = ordered_m2[column].groupby(runs).transform('size')
    flat_mask |= ordered_m2[column].notna() & run_length.ge(flat_threshold)

ds_m2 = ds_m2.loc[~flat_mask]

print("Number of data points before flat filter:", before_flat_filter)
print("Number of data points removed by flat filter:", before_flat_filter - len(ds_m2))
print("Number of data points after flat filter:", len(ds_m2))

# At this point, the dataset has been filtered for quality and flat runs.
# create an dataset variable name that can be used for further analysis
#contains the UTC datatimes all of the data quality and flat run filters applied
ds_m2_filtered = ds_m2.copy()
print("Filtered dataset created." , ds_m2_filtered.head())
print("Number of data points in filtered dataset:", len(ds_m2_filtered))
################################################################
## Now that we have the data pulled and filtered, let's try to apply a KDE equation to wind speed and temperature at height 50m 

# Extract wind speed and temperature for all data points (d x 2 matrix: N = [wind_speed, temperature])
wind_speed_data = ds_m2_filtered['Avg Avg Wind Speed @ 50m [m/s]'].values
temperature_data = ds_m2_filtered['Avg Temperature @ 50m [deg C]'].values
N_matrix = np.column_stack((wind_speed_data, temperature_data))  # (n x 2) matrix where each row is [wind_speed_i, temperature_i]

n = len(ds_m2_filtered)  # Total number of data points for KDE calculation

# Calculate the empirical covariance matrix (2 x 2) for the bi-variate data
# Σ = 2x2 empirical sample covariance matrix computed from sample deviations
empirical_covariance = np.cov(N_matrix.T)  # (2 x 2) matrix

# Calculate the bandwidth matrix H using Silverman's Rule for 2D data:
# H = (4/(n(m+2)))^(2/(m+4)) * Σ  where m=2 (dimensions)
# H = (4/(n*4))^(2/6) * Σ = (1/n)^(1/3) * Σ
m = 2  # dimensions (wind speed and temperature)
H = ((4 / (n * (m + 2)))**((2 / (m + 4)))) * empirical_covariance

# Compute bi-variate KDE at each point: f(N) = (1/nH) * sum_i K((N - N_i) / H)
# where K is the 2D Gaussian kernel: K(x) = (1/(2π)) * exp(-0.5 * x^T * x)
bi_kde_values = []

for n_idx in range(n):
    # Current evaluation point: N = [wind_speed_n, temperature_n]
    N = N_matrix[n_idx]  # (2,) array
    
    # Initialize KDE sum
    kde_sum = 0.0
    
    for i in range(n):
        # Reference point from dataset: N_i = [wind_speed_i, temperature_i]
        N_i = N_matrix[i]  # (2,) array
        
        # Standardized difference: (N - N_i) / H
        diff = N - N_i  # (2,) array
        H_inv = np.linalg.inv(H)  # (2 x 2) matrix
        standardized_diff = H_inv @ diff  # (2,) array
        
        # 2D Gaussian kernel: K(x) = (1/(2π)) * exp(-0.5 * ||x||^2)
        kernel_value = (1 / (2 * np.pi)) * np.exp(-0.5 * (standardized_diff @ standardized_diff))
        
        # Add to sum
        kde_sum += kernel_value
    
    # Bi-variate KDE: f(N) = (1/(nH)) * sum of kernels
    # where 1/(nH) accounts for the bandwidth scaling
    det_H = np.linalg.det(H)
    bi_kde = (1 / (n * np.sqrt(det_H))) * kde_sum
    
    bi_kde_values.append(bi_kde)

# Test the bi-variable KDE calculation for the first few data points
print("Bi-variable KDE results (first 5 data points of wind speed and temperature at 50m):")
for idx in range(min(5, len(bi_kde_values), len(N_matrix))):
    wind_speed_value, temperature_value = N_matrix[idx]
    print(
        f"  Point {idx}: Wind speed = {wind_speed_value:.6f} m/s, "
        f"Temperature = {temperature_value:.6f} °C, KDE = {bi_kde_values[idx]:.6e}"
    )

# With this function we can now try to create a 2D KDE plot for wind speed and temperature at 50m height
#for a better understanding we can also plot the raw data points of wind speed and temperature at 50m height 
#on the same plot as the KDE results

# Create a 2D KDE plot for wind speed and temperature at 50m height
from scipy.stats import gaussian_kde

# Stack the data for KDE input
wind_speed = ds_m2_filtered['Avg Avg Wind Speed @ 50m [m/s]']
temperature = ds_m2_filtered['Avg Temperature @ 50m [deg C]']

data = np.vstack([wind_speed, temperature])
kde = gaussian_kde(data, bw_method='silverman')

# Create a grid for evaluation
wind_speed_grid = np.linspace(wind_speed.min(), wind_speed.max(), 100)
temperature_grid = np.linspace(temperature.min(), temperature.max(), 100)
W, T = np.meshgrid(wind_speed_grid, temperature_grid)
positions = np.vstack([W.ravel(), T.ravel()])
kde_values = kde(positions).reshape(W.shape)

# Plot the KDE as a contour plot
plt.figure(figsize=(8, 6))
plt.scatter(wind_speed, temperature, c='blue', label='Raw Data', alpha=0.3, s=3)
filled_contours = plt.contourf(W, T, kde_values, levels=20, cmap='viridis', alpha=0.7)
contour_lines = plt.contour(W, T, kde_values, levels=filled_contours.levels, colors='white', linewidths=0.5)
colorbar = plt.colorbar(filled_contours)
colorbar.add_lines(contour_lines)
colorbar.set_label('Probability density [1 / ((m/s) * °C)]')

plt.xlabel('Wind Speed at 50m (m/s)')
plt.ylabel('Temperature at 50m (°C)')
plt.title('2D KDE of Wind Speed and Temperature at 50m Height')
plt.legend()
plt.show()
import matplotlib.pyplot as plt

# Extract wind speed and temperature for plotting
wind_speed = N_matrix[:, 0]
temperature = N_matrix[:, 1]
###########################################################
# create a .csv file of the date, time (UTC), Temperature, and Wind Speed at 50m, and KDE values for each data point
import pandas as pd

date_time = ds_m2_filtered['datetime_utc']
csv_data = pd.DataFrame({
    'Date Time (UTC)': date_time,
    'Temperature at 50m (°C)': temperature,
    'Wind Speed at 50m (m/s)': wind_speed,
    'KDE': bi_kde_values
})

csv_data.to_csv('2024_wind_temp_kde_50m.csv', index=False)

