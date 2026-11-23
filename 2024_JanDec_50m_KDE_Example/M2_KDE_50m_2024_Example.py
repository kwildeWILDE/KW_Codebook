#import necessary libraries
from webbrowser import get

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.animation as animation
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

# KDE requires a finite wind speed and temperature for each observation.
kde_columns = ['Avg Avg Wind Speed @ 50m [m/s]', 'Avg Temperature @ 50m [deg C]']
valid_kde_rows = np.isfinite(ds_m2_filtered[kde_columns].to_numpy()).all(axis=1)
print("Number of rows excluded from KDE due to missing or non-finite values:", (~valid_kde_rows).sum())
ds_m2_filtered = ds_m2_filtered.loc[valid_kde_rows].copy()

# Extract wind speed and temperature for all data points (d x 2 matrix: N = [wind_speed, temperature])
wind_speed_data = ds_m2_filtered['Avg Avg Wind Speed @ 50m [m/s]'].values
temperature_data = ds_m2_filtered['Avg Temperature @ 50m [deg C]'].values
N_matrix = np.column_stack((wind_speed_data, temperature_data))  # (n x 2) matrix where each row is [wind_speed_i, temperature_i]

n = len(ds_m2_filtered)  # Total number of data points for KDE calculation
if n < 3:
    raise ValueError("At least three finite wind speed and temperature pairs are required for a 2D KDE.")

# Calculate the empirical covariance matrix (2 x 2) for the bi-variate data
# Σ = 2x2 empirical sample covariance matrix computed from sample deviations
empirical_covariance = np.cov(N_matrix.T)  # (2 x 2) matrix

# Calculate the bandwidth matrix H using Silverman's Rule for 2D data:
# H = (4/(n(m+2)))^(2/(m+4)) * Σ  where m=2 (dimensions)
# H = (4/(n*4))^(2/6) * Σ = (1/n)^(1/3) * Σ
m = 2  # dimensions (wind speed and temperature)
H = ((4 / (n * (m + 2)))**((2 / (m + 4)))) * empirical_covariance

# H is the kernel covariance, not a standard-deviation matrix. The Gaussian
# exponent is diff.T @ H_inv @ diff, and sqrt(det(H)) normalizes the density.
try:
    np.linalg.cholesky(H)
except np.linalg.LinAlgError as exc:
    raise ValueError("The KDE bandwidth covariance must be positive definite; check the input data.") from exc
H_inv = np.linalg.inv(H)
normalization = 1 / (n * 2 * np.pi * np.sqrt(np.linalg.det(H)))
bi_kde_values = []

for n_idx in range(n):
    diff = N_matrix[n_idx] - N_matrix
    squared_distance = np.einsum('ij,jk,ik->i', diff, H_inv, diff)
    bi_kde_values.append(normalization * np.exp(-0.5 * squared_distance).sum())

bi_kde_values = np.asarray(bi_kde_values)

# SciPy supports the same full covariance matrix and Silverman bandwidth as H.
kde = gaussian_kde(N_matrix.T, bw_method='silverman')
scipy_kde_values = kde(N_matrix.T)
absolute_difference = np.abs(bi_kde_values - scipy_kde_values)
print("Maximum absolute difference between manual and SciPy KDE:", absolute_difference.max())
print("Manual and SciPy KDE agree:", np.allclose(bi_kde_values, scipy_kde_values, rtol=1e-10, atol=1e-12))
print("Silverman bandwidth factor (dimensionless):", kde.factor)
print("Shared bandwidth covariance matrix H (wind speed, temperature):\n", H)

# Test the bi-variable KDE calculation for the first few data points
print("Bi-variable KDE results (first 5 data points of wind speed and temperature at 50m):")
for idx in range(min(5, len(bi_kde_values), len(N_matrix))):
    wind_speed_value, temperature_value = N_matrix[idx]
    print(
        f"  Point {idx}: Wind speed = {wind_speed_value:.6f} m/s, "
        f"Temperature = {temperature_value:.6f} °C, "
        f"Manual KDE = {bi_kde_values[idx]:.6e}, SciPy KDE = {scipy_kde_values[idx]:.6e}"
    )

# Animate individual normalized Gaussian kernels, not the sum over all points.
# Their covariance H is shared, so only their centers change between frames.
animation_points = N_matrix[:25]
padding = 4 * np.sqrt(np.diag(H))
x_limits = (animation_points[:, 0].min() - padding[0], animation_points[:, 0].max() + padding[0])
y_limits = (animation_points[:, 1].min() - padding[1], animation_points[:, 1].max() + padding[1])
kernel_x, kernel_y = np.meshgrid(
    np.linspace(*x_limits, 150), np.linspace(*y_limits, 150)
)
kernel_positions = np.dstack((kernel_x, kernel_y))
kernel_peak = 1 / (2 * np.pi * np.sqrt(np.linalg.det(H)))
kernel_levels = np.linspace(0, kernel_peak, 12)
fig, ax = plt.subplots(figsize=(8, 6))
color_scale = plt.cm.ScalarMappable(norm=mcolors.Normalize(0, kernel_peak), cmap='viridis')
fig.colorbar(color_scale, ax=ax, label='Individual kernel PDF [1 / ((m/s) * °C)]')

def update(frame):
    single_point = animation_points[frame]
    kernel_pdf = multivariate_normal.pdf(kernel_positions, mean=single_point, cov=H)
    ax.clear()
    ax.contourf(kernel_x, kernel_y, kernel_pdf, levels=kernel_levels, cmap='viridis', alpha=0.8)
    ax.scatter(N_matrix[:, 0], N_matrix[:, 1], c='blue', alpha=0.15, s=3, label='Data points')
    ax.scatter(single_point[0], single_point[1], c='red', s=50, label='Kernel center')
    ax.set_xlim(x_limits)
    ax.set_ylim(y_limits)
    ax.set_xlabel('Wind Speed at 50m (m/s)')
    ax.set_ylabel('Temperature at 50m (°C)')
    ax.set_title(
        f'Individual Gaussian kernel: point {frame + 1} of {len(animation_points)}\n'
        f'Wind speed = {single_point[0]:.3f} m/s, Temperature = {single_point[1]:.3f} °C'
    )
    ax.legend()

ani = animation.FuncAnimation(fig, update, frames=len(animation_points), interval=500, repeat=False)
ani.save('kernel_orientation.gif', writer='pillow', fps=2)
print("Saved kernel_orientation.gif")
plt.show()


# Create a 2D KDE plot for wind speed and temperature at 50m height
wind_speed = ds_m2_filtered['Avg Avg Wind Speed @ 50m [m/s]']
temperature = ds_m2_filtered['Avg Temperature @ 50m [deg C]']

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
###################################################################
# On the same plot make a subplots of the timeseries for wind speed at 50 m, temperature at 50 m, and KDE values
# with datetime (UTC) indexing and conditional formatting for KDE values

# Ensure the data is sorted by datetime_utc and get the datetime index
datetime_utc = ds_m2_filtered['datetime_utc'].values
wind_speed = ds_m2_filtered['Avg Avg Wind Speed @ 50m [m/s]'].values
temperature = ds_m2_filtered['Avg Temperature @ 50m [deg C]'].values
kde_line_values = bi_kde_values  # Use the KDE values calculated for each data point

# Calculate which months have the lowest and highest KDE values
ds_m2_filtered_sorted = ds_m2_filtered.copy()
ds_m2_filtered_sorted['kde_value'] = bi_kde_values
ds_m2_filtered_sorted['month'] = pd.to_datetime(ds_m2_filtered_sorted['datetime_utc']).dt.month
ds_m2_filtered_sorted['month_name'] = pd.to_datetime(ds_m2_filtered_sorted['datetime_utc']).dt.strftime('%B')

monthly_kde_mean = ds_m2_filtered_sorted.groupby(['month', 'month_name'])['kde_value'].mean()
month_highest_kde = monthly_kde_mean.idxmax()[1]  # Get month name
month_lowest_kde = monthly_kde_mean.idxmin()[1]   # Get month name
max_kde = monthly_kde_mean.max()
min_kde = monthly_kde_mean.min()

print(f"Month with highest mean KDE value: {month_highest_kde} ({max_kde:.6e})")
print(f"Month with lowest mean KDE value: {month_lowest_kde} ({min_kde:.6e})")

# Create figure with subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))

# Subplot 1: Wind Speed at 50m
ax1.plot(datetime_utc, wind_speed, color='blue', label='Wind Speed at 50m', linewidth=1)
ax1.set_ylabel('Wind Speed (m/s)', fontsize=11)
ax1.set_title('Time Series: Wind Speed, Temperature, and KDE Values at 50m Height (2024)', fontsize=12, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

# Subplot 2: Temperature at 50m
ax2.plot(datetime_utc, temperature, color='red', label='Temperature at 50m', linewidth=1)
ax2.set_ylabel('Temperature (°C)', fontsize=11)
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax2.xaxis.set_major_locator(mdates.MonthLocator())

# Subplot 3: KDE Values with Smooth Gradient Conditional Formatting
# Normalize KDE values to 0-1 range for color mapping
kde_min = kde_line_values.min()
kde_max = kde_line_values.max()
kde_normalized = (kde_line_values - kde_min) / (kde_max - kde_min)

# Use RdYlGn colormap for smooth gradient from red (low) to yellow (medium) to green (high)
cmap = plt.cm.RdYlGn
norm = mcolors.Normalize(vmin=0, vmax=1)

# Plot segments with smooth gradient coloring
for i in range(len(datetime_utc) - 1):
    # Get color from colormap based on normalized KDE value
    color = cmap(kde_normalized[i])
    
    # Plot line segment
    ax3.plot(datetime_utc[i:i+2], kde_line_values[i:i+2], color=color, linewidth=2.5)

ax3.set_ylabel('KDE Value', fontsize=11)
ax3.set_xlabel('Month (UTC)', fontsize=11)
ax3.legend(['KDE Values (Smooth Gradient)'], loc='upper left')
ax3.grid(True, alpha=0.3)
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax3.xaxis.set_major_locator(mdates.MonthLocator())

# Add colorbar to show gradient scale
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax3, orientation='horizontal', pad=0.2)
cbar.set_label('Normalized KDE Value (0=Low, 1=High)', fontsize=10)

# Align all subplots to have the same x-axis limits
x_min = datetime_utc.min()
x_max = datetime_utc.max()
ax1.set_xlim(x_min, x_max)
ax2.set_xlim(x_min, x_max)
ax3.set_xlim(x_min, x_max)

plt.tight_layout()
plt.show()



###########################################################
# # create a .csv file of the date, time (UTC), Temperature, and Wind Speed at 50m, and KDE values for each data point
# import pandas as pd

# date_time = ds_m2_filtered['datetime_utc']
# csv_data = pd.DataFrame({
#     'Date Time (UTC)': date_time,
#     'Temperature at 50m (°C)': temperature,
#     'Wind Speed at 50m (m/s)': wind_speed,
#     'KDE': bi_kde_values,
#     'SciPy KDE': scipy_kde_values,
#     'KDE absolute difference': absolute_difference,
#     'Silverman bandwidth factor': kde.factor,
#     'H wind speed variance': H[0, 0],
#     'H wind speed-temperature covariance': H[0, 1],
#     'H temperature variance': H[1, 1]
# })

# csv_data.to_csv('2024_wind_temp_kde_50m.csv', index=False)

