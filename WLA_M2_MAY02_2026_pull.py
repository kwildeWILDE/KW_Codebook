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
file_path = f"{dp}/M2_MAY022026_Datapull.xlsx"

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
# plt.title('Temperature Over Time MAY 02 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

###########################################################
#Plotting the wind speeds over time at different heights 

wind_sp2 = ds['Avg Wind Speed @ 2m [m/s]']
wind_sp5 = ds['Avg Wind Speed @ 5m [m/s]']
wind_sp10 = ds['Avg Wind Speed @ 10m [m/s]']
wind_sp20 = ds['Avg Wind Speed @ 20m [m/s]']
wind_sp50 = ds['Avg Wind Speed @ 50m [m/s]']
wind_sp80 = ds['Avg Wind Speed @ 80m [m/s]']

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
# plt.title('Wind Speed Over Time MAY 02 2026')
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

# plt.figure(figsize=(12, 6))
# plt.plot(time, wind_dir2, label='Wind Direction @ 2m [deg]', color='blue')
# plt.plot(time, wind_dir5, label='Wind Direction @ 5m [deg]', color='cyan')
# plt.plot(time, wind_dir10, label='Wind Direction @ 10m [deg]', color='magenta')
# plt.plot(time, wind_dir20, label='Wind Direction @ 20m [deg]', color='yellow')
# plt.plot(time, wind_dir50, label='Wind Direction @ 50m [deg]', color='green')
# plt.plot(time, wind_dir80, label='Wind Direction @ 80m [deg]', color='red')

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# plt.xlabel('Time')
# plt.ylabel('Wind Direction [deg]')
# plt.title('Wind Direction Over Time MAY 02 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10, loc='upper center')
# plt.show()

#### AFTER THE RESULTS OF THIS, IGNORE THE WIND DIRECTION AT 5M FOR THE REST OF THE ANALYSIS

#########################################################
# create the histogam and pdf line for the temperature at different heights 
# plt.figure(figsize=(12, 6))
# plt.hist(temp2, bins=15, color='b', alpha=0.6, label='Temperature @ 2m')
# plt.hist(temp50, bins=15, color='g', alpha=0.6, label='Temperature @ 50m')
# plt.hist(temp80, bins=15, color='r', alpha=0.6, label='Temperature @ 80m')

# for temp, color in zip([temp2, temp50, temp80], ['b', 'g', 'r']):
#     temp = np.asarray(temp).ravel()  # convert xarray DataArray to a plain 1D numpy array
#     temp = temp[~np.isnan(temp)]
#     temp_min = np.nanmin(temp)
#     temp_max = np.nanmax(temp)
#     # KDE follows the actual (possibly skewed/multimodal) shape better than a Gaussian fit
#     #KDE = the kernel density estimate of the temperature distribution
#     temp_kde = gaussian_kde(temp)
#     x = np.linspace(temp_min, temp_max, 1000)
#     plt.plot(x, temp_kde(x) * len(temp) * (temp_max - temp_min) / 15, c=color, lw=2)

# plt.xlabel('Temperature')
# plt.ylabel('Frequency')
# plt.title('Histogram and Respective Distribution PDF line of Temperatures at Different Heights MAY 02 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()
################################################################
# Create a histogram of the frequency of the wind speeds at different heights
# plt.figure(figsize=(12, 6))
# plt.hist(wind_sp2, bins=30, color='b', alpha=0.6, label='Wind Speed @ 2m')
# plt.hist(wind_sp5, bins=30, color='c', alpha=0.6, label='Wind Speed @ 5m')
# plt.hist(wind_sp10, bins=30, color='m', alpha=0.6, label='Wind Speed @ 10m')
# plt.hist(wind_sp20, bins=30, color='y', alpha=0.6, label='Wind Speed @ 20m')
# plt.hist(wind_sp50, bins=30, color='g', alpha=0.6, label='Wind Speed @ 50m')
# plt.hist(wind_sp80, bins=30, color='r', alpha=0.6, label='Wind Speed @ 80m')

# #distribution pdf line for the wind speeds
# for wind_sp, color in zip([wind_sp2, wind_sp5, wind_sp10, wind_sp20, wind_sp50, wind_sp80], ['b', 'c', 'm', 'y', 'g', 'r']):
#     wind_sp = np.asarray(wind_sp).ravel()  # convert xarray DataArray to a plain 1D numpy array
#     wind_sp = wind_sp[~np.isnan(wind_sp)]  # remove NaN values
#     sp_min = np.nanmin(wind_sp)
#     sp_max = np.nanmax(wind_sp)
#     #KDE follows the distribution of the wind speeds
#     wind_sp_kde = gaussian_kde(wind_sp)
#     x = np.linspace(sp_min, sp_max, 1000)
#     plt.plot(x, wind_sp_kde(x) * len(wind_sp) * (sp_max - sp_min) / 30, c=color, lw=2)


# plt.xlabel('Wind Speed')
# plt.ylabel('Frequency')
# plt.title('Histogram and Respective Distribution PDF line of Wind Speeds at Different Heights SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()
###################################################################################
#historogram and PDF line for wind direction
# plt.figure(figsize=(12, 6))
# plt.hist(wind_dir2, bins=15, color='b', alpha=0.6, label='Wind Direction @ 2m')
# plt.hist(wind_dir5, bins=15, color='c', alpha=0.6, label='Wind Direction @ 5m')
# plt.hist(wind_dir10, bins=15, color='m', alpha=0.6, label='Wind Direction @ 10m')
# plt.hist(wind_dir20, bins=15, color='y', alpha=0.6, label='Wind Direction @ 20m')
# plt.hist(wind_dir50, bins=15, color='g', alpha=0.6, label='Wind Direction @ 50m')
# plt.hist(wind_dir80, bins=15, color='r', alpha=0.6, label='Wind Direction @ 80m')

# # distribution pdf line for the wind directions
# for wind_dir, color in zip([wind_dir2, wind_dir5, wind_dir10, wind_dir20, wind_dir50, wind_dir80], ['b', 'c', 'm', 'y', 'g', 'r']):
#     wind_dir = np.asarray(wind_dir).ravel()  # convert xarray DataArray to a plain 1D numpy array
#     wind_dir = wind_dir[~np.isnan(wind_dir)]  # remove NaN values
#     #dir_mean = np.nanmean(wind_dir)
#     #dir_std = np.nanstd(wind_dir)
#     #dir_dist = norm(dir_mean, dir_std)
#     dir_kde = gaussian_kde(wind_dir)
#     dir_min = np.nanmin(wind_dir)
#     dir_max = np.nanmax(wind_dir)
#     x = np.linspace(dir_min, dir_max, 1000)
#     plt.plot(x, dir_kde(x) * len(wind_dir) * (dir_max - dir_min) / 15, c=color, lw=2)

# plt.xlabel('Wind Direction')
# plt.ylabel('Frequency')
# plt.title('Histogram and Respective Distribution PDF line of Wind Directions at Different Heights SEPT 19 2026')
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()
######################################################################################
#Plotting the collective M2 plots of temperature, wind speed, and wind direction
# plt.figure(figsize=(12, 6*3.2))

# #1 Wind speed time series
# plt.subplot(3, 1, 1)
# plt.plot(time, wind_sp2, 'b', label='Wind Speed @ 2m')
# plt.plot(time, wind_sp50, 'g', label='Wind Speed @ 50m')
# plt.plot(time, wind_sp80, 'r', label='Wind Speed @ 80m')
# #plt.xlabel('Time')
# plt.ylabel('Wind Speed')
# plt.title('M2 Wind Speed Time Series at Different Heights MAY 02 2026', fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend(fontsize=10)

# #2 Wind direction time series
# plt.subplot(3, 1, 2)
# plt.plot(time, wind_dir2, 'b', label='Wind Direction @ 2m')
# plt.plot(time, wind_dir50, 'g', label='Wind Direction @ 50m')
# plt.plot(time, wind_dir80, 'r', label='Wind Direction @ 80m')
# #plt.xlabel('Time')
# plt.ylabel('Wind Direction')
# plt.title('M2 Wind Direction Time Series at Different Heights MAY 02 2026', fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend(fontsize=10)

# #3 Temperature time series
# plt.subplot(3, 1, 3)
# plt.plot(time, temp2, 'b', label='Temperature @ 2m')
# plt.plot(time, temp50, 'g', label='Temperature @ 50m')
# plt.plot(time, temp80, 'r', label='Temperature @ 80m')
# plt.xlabel('Time')
# plt.ylabel('Temperature')
# plt.title('M2 Temperature Time Series at Different Heights MAY 02 2026', fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.legend(fontsize=10)

# plt.tight_layout(h_pad=4.0)
# plt.subplots_adjust(hspace=0.4)
# plt.show()

#Plotting the M2 instruments Richardson number
#get the recorded Richardson numbers for further analysis 
intRi_2_50 = ds['Richardson Number (2-50m)']
intRi_2_80 = ds['Richardson Number (2-80m)']
intRi_50_80 = ds['Richardson Number (50-80m)']


# plotting the actual recorded Richardson numbers for comparison
# plt.figure(figsize=(12, 6))
# plt.plot(time, intRi_2_50, c='purple',ls='-', label='intRi_2_50')
# plt.plot(time, intRi_2_80, c='orange',ls='-', label='intRi_2_80')
# plt.plot(time, intRi_50_80, c='brown',ls='-', alpha = 0.25, label='intRi_50_80')
# plt.axhline(0, color='red', linewidth=0.5, linestyle='--')  # add a horizontal line at Ri = 0 for reference
# # The Reason why the Ri for 50-80m is plotted with a lower alpha is because when it comes to the Richardson Number it is best to caulculate 
# ## it with a greater height difference for more accurate results, letting us focus more on the Ri from 2-50m and 2-80m.

# #setting up the x-axis to show time in a readable format
# plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
# plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))

# #have the plot in a log scale for smoother looking results 
# plt.yscale ('symlog', linthresh=0.01)
# plt.xlabel('Time')
# plt.ylabel('Recorded Richardson Number')
# plt.title('M2 Recorded Richardson Number over Time SEPT 19 2026')
# plt.xticks(rotation=45, fontsize=10)
# plt.yticks(fontsize=10)
# plt.grid(True, linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.legend(fontsize=10)
# plt.show()

############################################################
#make a time varaible that corresponds to when the richardson number at 2-50 m is less than 0
time_intRi_2_50_negative = time[np.asarray(intRi_2_50) < 0]
intRi_2_50_negative = intRi_2_50[np.asarray(intRi_2_50) < 0]

#make a time varaible that corresponds to when the richardson number at 2-80 m is less than 0
time_intRi_2_80_negative = time[np.asarray(intRi_2_80) < 0]
intRi_2_80_negative = intRi_2_80[np.asarray(intRi_2_80) < 0]

#make a time varaible that corresponds to when the richardson number at 50-80 m is less than 0
time_intRi_50_80_negative = time[np.asarray(intRi_50_80) < 0]
intRi_50_80_negative = intRi_50_80[np.asarray(intRi_50_80) < 0]
###########################################################
## FOr when the richardson number is negative, we can now analyze the corresponding time periods and values for further investigation.
# making of the bivirate KDE ditrubution for an overlay of the raw scatter of between wind speed and temperature 
# of when the Richardson number for heights 2-50m is negative

# Bivariate (2D) Kernel Density Estimate (KDE) joint PDF of wind speed and temperature at each height, overlaid on the raw scatter
height_data = {
    '2m': (wind_sp2, temp2, 'b'),
    '50m': (wind_sp50, temp50, 'g'),
    '80m': (wind_sp80, temp80, 'r'),
}

# mask of the samples where the 2-50 m Richardson number is negative (same samples as time_intRi_2_50_negative)
# neg_mask = np.asarray(intRi_2_50).ravel() < 0

# fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=False, sharey=False)

# for ax, (label, (wind_sp, temp, color)) in zip(axes, height_data.items()):
#     wind_sp = np.asarray(wind_sp).ravel()
#     temp = np.asarray(temp).ravel()
#     valid = ~(np.isnan(wind_sp) | np.isnan(temp)) & neg_mask #keep non-NaN samples taken when Ri(2-50m) < 0
#     wind_sp, temp = wind_sp[valid], temp[valid]

#     # 2D KDE: non-parametric joint PDF, so multiple modes are preserved instead of forced into one Gaussian
#     kde = gaussian_kde(np.vstack([wind_sp, temp]))

#     x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
#     y = np.linspace(temp.min(), temp.max(), 100)
#     X, Y = np.meshgrid(x, y)
#     Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape) #evaluate the KDE joint PDF at each grid point

#     ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
#     ax.scatter(wind_sp, temp, s=10, c=color, edgecolor='k', linewidth=0.3)
#     ax.set_xlabel(f'Wind Speed @ {label}')
#     ax.set_ylabel(f'Temperature @ {label}')
#     ax.set_title(f'KDE Joint PDF @ {label} (n={wind_sp.size})', fontsize=10)
#     ax.grid(True, linestyle='--', alpha=0.5)

# fig.suptitle('Bivariate KDE Joint PDF of Wind Speed and Temperature (Ri 2-50 m < 0) MAY 02 2026')
# plt.tight_layout()
# plt.show()

###########################################################################################
#Make the same bivariate KDE joint PDF for when the Richardson number for heights 2-80m is negative 
# mask of the samples where the 2-80 m Richardson number is negative (same samples as time_intRi_2_80_negative)
# neg_mask = np.asarray(intRi_2_80).ravel() < 0

# fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=False, sharey=False)

# for ax, (label, (wind_sp, temp, color)) in zip(axes, height_data.items()):
#     wind_sp = np.asarray(wind_sp).ravel()
#     temp = np.asarray(temp).ravel()
#     valid = ~(np.isnan(wind_sp) | np.isnan(temp)) & neg_mask #keep non-NaN samples taken when Ri(2-80m) < 0
#     wind_sp, temp = wind_sp[valid], temp[valid]

#     # 2D KDE: non-parametric joint PDF, so multiple modes are preserved instead of forced into one Gaussian
#     kde = gaussian_kde(np.vstack([wind_sp, temp]))

#     x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
#     y = np.linspace(temp.min(), temp.max(), 100)
#     X, Y = np.meshgrid(x, y)
#     Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape) #evaluate the KDE joint PDF at each grid point

#     ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
#     ax.scatter(wind_sp, temp, s=10, c=color, edgecolor='k', linewidth=0.3)
#     ax.set_xlabel(f'Wind Speed @ {label}')
#     ax.set_ylabel(f'Temperature @ {label}')
#     ax.set_title(f'KDE Joint PDF @ {label} (n={wind_sp.size})', fontsize=10)
#     ax.grid(True, linestyle='--', alpha=0.5)

# fig.suptitle('Bivariate KDE Joint PDF of Wind Speed and Temperature (Ri 2-80 m < 0) MAY 02 2026')
# plt.tight_layout()
# plt.show()

##########################################################################################
# From both bivariate KDE joint PDFs (Ri 2-50 m < 0 and Ri 2-80 m < 0) we find the outlier points (lowest KDE density),
# keep only the times that are outliers in BOTH, and highlight them along the time series.
# A Richardson number panel (2-50 m and 2-80 m) is placed on top to show the correspondence.
time_series_data = {
    '2m': (wind_sp2, temp2, 'b'),
    '50m': (wind_sp50, temp50, 'g'),
    '80m': (wind_sp80, temp80, 'r'),
}

x = time
x_arr = np.asarray(x)
Ri_50 = np.asarray(intRi_2_50).ravel()
Ri_80 = np.asarray(intRi_2_80).ravel()

y1 = (min(wind_sp2.min(), wind_sp50.min(), wind_sp80.min()), max(wind_sp2.max(), wind_sp50.max(), wind_sp80.max()))
y2 = (min(temp2.min(), temp50.min(), temp80.min()), max(temp2.max(), temp50.max(), temp80.max()))

# half the median sample spacing, used to size the shaded outlier spans below
half_dt = pd.Series(time).diff().dropna().median() / 2
outlier_patch = Patch(facecolor='yellow', alpha=0.30, label='Outlier in BOTH KDE PDFs (Ri 2-50 m < 0 & Ri 2-80 m < 0)')

def kde_outlier_mask(wind_arr, temp_arr, ri_arr, pct=5):
    """Boolean mask (full length) of samples in the bottom pct% of KDE density, using only samples where Ri < 0."""
    valid = ~(np.isnan(wind_arr) | np.isnan(temp_arr)) & (ri_arr < 0)
    kde = gaussian_kde(np.vstack([wind_arr[valid], temp_arr[valid]]))
    dens = kde(np.vstack([wind_arr[valid], temp_arr[valid]]))
    mask = np.zeros(wind_arr.shape, dtype=bool)
    mask[np.flatnonzero(valid)[dens < np.percentile(dens, pct)]] = True
    return mask

fig, axes = plt.subplots(4, 1, figsize=(12, 13), sharex=True, gridspec_kw={'height_ratios': [1, 1.3, 1.3, 1.3]})
ax_ri = axes[0]
ax_ri.plot(x, Ri_50, color='purple', label='Ri (2-50 m)')
ax_ri.plot(x, Ri_80, color='orange', label='Ri (2-80 m)')
ax_ri.axhline(0, color='k', lw=0.8)
ax_ri.set_ylabel('Richardson Number')
ax_ri.set_title('Richardson Number (2-50 m and 2-80 m)')
ax_ri.grid(True, linestyle='--', alpha=0.5)

shared_outliers = np.zeros(len(x_arr), dtype=bool)
for ax1, (label, (wind_sp, temp, color)) in zip(axes[1:], time_series_data.items()):
    ax1.plot(x, wind_sp, label=f'Wind Speed @ {label}', color=color, linestyle='--')
    ax1.set_ylabel('Wind Speed (m/s)')
    ax1.set_ylim(y1)
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(x, temp, label=f'Temperature @ {label}', color=color, linestyle='-')
    ax2.set_ylabel('Temperature (\u00b0C)')
    ax2.set_ylim(y2)
    ax1.set_title(f'Time Series of Wind Speed and Temperature @ {label}')

    wind_arr = np.asarray(wind_sp).ravel()
    temp_arr = np.asarray(temp).ravel()
    both = kde_outlier_mask(wind_arr, temp_arr, Ri_50) & kde_outlier_mask(wind_arr, temp_arr, Ri_80)
    shared_outliers |= both

    for t in x_arr[both]:
        ax1.axvspan(t - half_dt, t + half_dt, color='yellow', alpha=0.30, zorder=0)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2 + [outlier_patch], labels1 + labels2 + [outlier_patch.get_label()], loc='upper right', fontsize=8)

# mirror the shared outlier times onto the Richardson number panel
for t in x_arr[shared_outliers]:
    ax_ri.axvspan(t - half_dt, t + half_dt, color='yellow', alpha=0.30, zorder=0)
h, l = ax_ri.get_legend_handles_labels()
ax_ri.legend(h + [outlier_patch], l + [outlier_patch.get_label()], loc='upper right', fontsize=8)

axes[-1].set_xlabel('Time')
axes[-1].xaxis.set_major_locator(mdates.HourLocator(interval=2))
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.setp(axes[-1].get_xticklabels(), rotation=45, fontsize=10)

fig.suptitle('M2 Shared KDE Outliers (Ri 2-50 m < 0 & Ri 2-80 m < 0) with Richardson Number MAY 02 2026')
plt.tight_layout()
plt.show()

#### NOT GOING TO DO THE SAME ANLYSIS BETWEEN THE WIND SPEED AND DIRECTION SINCE THE INSTRUMENTS HAVE BEEN FAULTY WITH WIND DIRECTION MESURMENTS#####
## Move onto the same analysis but from the dataset frm the s40.lidar.z01.c1 instrument 