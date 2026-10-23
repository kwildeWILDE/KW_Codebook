#import necessary libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xarray as xr
import os
import re 
import glob
import scipy.stats as stats
from scipy.stats import alpha, gaussian_kde, norm, weibull_min, multivariate_normal
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from matplotlib.patches import Ellipse, Patch
from windrose import WindroseAxes

#############################################
#Pull the Full M2 data from Jan 31 to Oct 17, 2026 

dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_FULL_JAN31_OCT31_2026_Datapull.xlsx"

#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)

print(ds_m2.head())

#Convert MST into an apporite data format for plotting
ds_m2['datetime'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str) + ' ' + ds_m2['MST'].astype(str))
#the FULL datapull rows are not in time order; sort so time series and flat-run detection are valid
ds_m2 = ds_m2.sort_values('datetime').reset_index(drop=True)
time = ds_m2['datetime']


#from looking over the plot and the excel data there are varibles that have been recorded as "-99999"
#replace these with NaN for proper analysis
ds_m2 = ds_m2.replace(-99999, np.nan)

# ^^^^^ New ds to use that skips the -99999 values

#vairbles for temperature at different heights
temp2 = ds_m2['Temperature @ 2m [deg C]']
temp50 = ds_m2['Temperature @ 50m [deg C]']
temp80 = ds_m2['Temperature @ 80m [deg C]']

#varibles for wind speed at different heights
wind_speed2 = ds_m2['Avg Wind Speed @ 2m [m/s]']
wind_speed5 = ds_m2['Avg Wind Speed @ 5m [m/s]']
wind_speed10 = ds_m2['Avg Wind Speed @ 10m [m/s]']
wind_speed20 = ds_m2['Avg Wind Speed @ 20m [m/s]']
wind_speed50 = ds_m2['Avg Wind Speed @ 50m [m/s]']
wind_speed80 = ds_m2['Avg Wind Speed @ 80m [m/s]']


# variables for wind direction at different heights
wind_dir2 = ds_m2['Avg Wind Direction @ 2m [deg]']
wind_dir5 = ds_m2['Avg Wind Direction @ 5m [deg]']
wind_dir10 = ds_m2['Avg Wind Direction @ 10m [deg]']
wind_dir20 = ds_m2['Avg Wind Direction @ 20m [deg]']
wind_dir50 = ds_m2['Avg Wind Direction @ 50m [deg]']
wind_dir80 = ds_m2['Avg Wind Direction @ 80m [deg]']

#Flat (stuck-sensor) values: a run of identical consecutive readings is not real wind variability.
#Find runs on the full series (so runs crossing a month boundary are caught) and mask them as NaN.
MIN_FLAT_RUN = 6  # consecutive identical samples treated as flat; adjust to the M2 sampling interval

def mask_flat_runs(series, min_run=MIN_FLAT_RUN):
    run_id = (series != series.shift()).cumsum()
    run_len = series.groupby(run_id).transform('size')
    return series.mask((run_len >= min_run) & series.notna())

wind_speed10_clean = mask_flat_runs(wind_speed10)
wind_speed50_clean = mask_flat_runs(wind_speed50)
wind_speed80_clean = mask_flat_runs(wind_speed80)
wind_dir50_clean = mask_flat_runs(wind_dir50)  # stuck direction readings (e.g. repeated 0 deg)
wind_dir80_clean = mask_flat_runs(wind_dir80)
for month in range(2, 11):
    n_flat = (wind_speed10[time.dt.month == month].notna() & wind_speed10_clean[time.dt.month == month].isna()).sum()
    print(f"Month {month}: removed {n_flat} flat wind speed samples")

# create a month to month (Feb to Oct 2026) frequency hitogram with wibull fit line for wind speed at 10 m
# for month in range(2, 11):
#     wind_speed_month = wind_speed10_clean[time.dt.month == month].dropna()
#     #Weibull needs positive values; calm (0 m/s) samples are excluded from the fit
#     wind_speed_month = wind_speed_month[wind_speed_month > 0]
#     if len(wind_speed_month) == 0:
#         continue
#     plt.figure(figsize=(10, 6))
#     plt.hist(wind_speed_month, bins=20, density=True, alpha=0.6, color='b', label='Wind Speed Frequency')
#     # Fit a Weibull distribution
#     params = weibull_min.fit(wind_speed_month, floc=0)
#     x = np.linspace(0, wind_speed_month.max(), 100)
#     plt.plot(x, weibull_min.pdf(x, *params), 'r-', lw=2, label='Weibull Fit')
#     plt.title(f'M2 Wind Speed at 10m - Month {month} , 2026')
#     plt.xlabel('Wind Speed [m/s]')
#     plt.ylabel('Frequency')
#     plt.legend()
#     plt.show()

################################################################
#Wind rose plots for 50m and 80m 
#on a month to month basis (Feb-Oct 2026)
#Note: Keep the scale and probability bins consistent across months for comparison

# Wind rose for 50m month to month
SPEED_BINS = np.arange(0, 22, 2)  # fixed speed bins (m/s) shared by all months
RMAX = 20                         # fixed max radial frequency (%) shared by all months; raise if bars clip
# for month in range(2, 11):
#     mask = (time.dt.month == month) &     wind_dir50_clean.notna() & wind_speed50.notna()    
#     plt.figure(figsize=(8, 8))
#     ax = WindroseAxes.from_ax()
#     ax.bar(wind_dir50_clean[mask], wind_speed50[mask], normed=True, opening=0.8, edgecolor='white', bins=SPEED_BINS)
#     ax.set_ylim(0, RMAX)
#     ax.set_rgrids(np.linspace(0, RMAX, 5)[1:], labels=[f'{r:.0f}%' for r in np.linspace(0, RMAX, 5)[1:]])
#     ax.set_legend(title='Wind Speed [m/s]')
#     ax.set_title(f' M2 Wind Rose at 50m - Month {month}')
#     plt.show()
################################
#Wind rose for 80m month to month
# for month in range(2, 11):
#     mask = (time.dt.month == month) & wind_dir80_clean.notna() & wind_speed80_clean.notna()
#     plt.figure(figsize=(8, 8))
#     ax = WindroseAxes.from_ax()
#     ax.bar(wind_dir80_clean[mask], wind_speed80_clean[mask], normed=True, opening=0.8, edgecolor='white', bins=SPEED_BINS)
#     ax.set_ylim(0, RMAX)
#     ax.set_rgrids(np.linspace(0, RMAX, 5)[1:], labels=[f'{r:.0f}%' for r in np.linspace(0, RMAX, 5)[1:]])
#     ax.set_legend(title='Wind Speed [m/s]')
#     ax.set_title(f' M2 Wind Rose at 80m - Month {month}')
#     plt.show()

#######################################
# Finding Relevent Events from finding extreme events

#Start creating Bi-vibrate KDE joint plots with raw scatter between wind speed and temperature 
# at JUST 50 m 

#get the clean varaibles first
wind_speed50_clean = mask_flat_runs(wind_speed50)
temperature50_clean = mask_flat_runs(temp50)

#Day/night regimes from solar elevation (NOAA approximation) at the M2 site, using MST (UTC-7, no DST).
#Daytime = sun center above -0.833 deg (standard sunrise/sunset definition, includes refraction).
M2_LAT, M2_LON, MST_OFFSET_HR = 39.91, -105.23, -7

def is_daytime(t, lat=M2_LAT, lon=M2_LON, tz=MST_OFFSET_HR):
    hour = t.dt.hour + t.dt.minute / 60 + t.dt.second / 3600
    g = 2 * np.pi / 365 * (t.dt.dayofyear - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                       - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = hour * 60 + eqtime + 4 * lon - 60 * tz
    ha = np.radians(tst / 4 - 180)
    lat_r = np.radians(lat)
    sin_elev = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(ha)
    return (np.degrees(np.arcsin(sin_elev)) > -0.833).to_numpy()

is_day = is_daytime(time)
REGIMES = {'Daytime': is_day, 'Nighttime': ~is_day}

# #create a month by month basis bi_vibrate KDE joint PDF ellipses plots with raw scatter overlay beween 50m wind speed and temperature 
# for month in range(2, 11):
#     month_mask = (time.dt.month == month).values
#     fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharex=True, sharey=True)
#     for ax, (regime, regime_mask) in zip(axes, REGIMES.items()):
#         mask = month_mask & regime_mask
#         wind_sp = wind_speed50_clean[mask].to_numpy()
#         temp = temperature50_clean[mask].to_numpy()
#         valid = ~(np.isnan(wind_sp) | np.isnan(temp))
#         wind_sp, temp = wind_sp[valid], temp[valid]
#         ax.set_xlabel('Wind Speed @ 50m [m/s]')
#         ax.set_ylabel('Temperature @ 50m [deg C]')
#         ax.grid(True, linestyle='--', alpha=0.5)
#         if wind_sp.size < 3:
#             ax.set_title(f'{regime} - insufficient data (n={wind_sp.size})')
#             continue

#         kde = gaussian_kde(np.vstack([wind_sp, temp]))
#         x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
#         y = np.linspace(temp.min(), temp.max(), 100)
#         X, Y = np.meshgrid(x, y)
#         Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

#         cf = ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
#         ax.contour(X, Y, Z, levels=15, colors='w', linewidths=0.6, zorder=3)
#         ax.scatter(wind_sp, temp, s=5, c='g', edgecolor='k', linewidth=0.3, alpha=0.7, zorder=2)
#         fig.colorbar(cf, ax=ax, label='Joint PDF')
#         ax.set_title(f'{regime} (n={wind_sp.size})')

#     fig.suptitle(f'M2 Bivariate KDE Joint PDF @ 50m - Month {month}')
#     plt.tight_layout()
#     plt.show()
############################################################################

#do the same Bi-vibrate KDE joint month by month plots between 50m turbulence intensity and wind speed 
turbi50 = ds_m2['Turbulence Intensity @ 50m']
turbi50_clean = turbi50.where(turbi50.notnull(), np.nan)

# for month in range(2, 11):
#     month_mask = (time.dt.month == month).values
#     fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharex=True, sharey=True)
#     for ax, (regime, regime_mask) in zip(axes, REGIMES.items()):
#         mask = month_mask & regime_mask
#         wind_sp = wind_speed50_clean[mask].to_numpy()
#         turbi = turbi50_clean[mask].to_numpy()
#         valid = ~(np.isnan(wind_sp) | np.isnan(turbi))
#         wind_sp, turbi = wind_sp[valid], turbi[valid]
#         ax.set_xlabel('Wind Speed @ 50m [m/s]')
#         ax.set_ylabel('Turbulence Intensity @ 50m')
#         ax.grid(True, linestyle='--', alpha=0.5)
#         if wind_sp.size < 3:
#             ax.set_title(f'{regime} - insufficient data (n={wind_sp.size})')
#             continue

#         kde = gaussian_kde(np.vstack([wind_sp, turbi]))
#         x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
#         y = np.linspace(turbi.min(), turbi.max(), 100)
#         X, Y = np.meshgrid(x, y)
#         Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

#         cf = ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
#         ax.contour(X, Y, Z, levels=15, colors='w', linewidths=0.6, zorder=3)
#         ax.scatter(wind_sp, turbi, s=5, c='g', edgecolor='k', linewidth=0.3, alpha=0.7, zorder=2)
#         fig.colorbar(cf, ax=ax, label='Joint PDF')
#         ax.set_title(f'{regime} (n={wind_sp.size})')

#     fig.suptitle(f'M2 Bivariate KDE Joint PDF @ 50m - Month {month} (Turbulence Intensity vs Wind Speed)')
#     plt.tight_layout()
#     plt.show()
#############################################
##
# Now that we have bi-variate KDE plots for turbulence intensity vs wind speed and wind speed vs temperature,
#  we can proceed with further analysis or comparisons as needed.

#both of thses KDE analysis have points that are outside the outer KDE contour ditribution level, 
# indicating potential outliers or extreme values that are not well captured by the KDE.
# Create a month to month time line of the values of wind speed ('--'), temperature ('-'), and turbulence intensity ('-.') 
# for the night and day periods , (show the night time with a light grey background, and day time with a white background)

# For the outliers points from the pervious KDE, plot a highlierted line of WHEN the outliers occur over time.
#For the outlier ofwind speed and temperature highlight with the color yellow in time 
#for the outlier of turbulence intensity and wind speed highlight with the color red in time 
#that so we can see when oulieres for both tpes of bi-variate KDE appear as the color orange (color mixing)

#Outliers = samples outside the outermost KDE contour (density below the lowest contour level),
#computed per month and per day/night regime, exactly like the KDE plots above.
def kde_outliers(a, b, base_mask, levels=15):
    out = np.zeros(len(a), dtype=bool)
    a, b = np.asarray(a), np.asarray(b)
    idx = np.where(base_mask & ~(np.isnan(a) | np.isnan(b)))[0]
    if idx.size < 3:
        return out
    kde = gaussian_kde(np.vstack([a[idx], b[idx]]))
    x = np.linspace(a[idx].min(), a[idx].max(), 100)
    y = np.linspace(b[idx].min(), b[idx].max(), 100)
    X, Y = np.meshgrid(x, y)
    Z = kde(np.vstack([X.ravel(), Y.ravel()]))
    lowest_level = Z.min() + (Z.max() - Z.min()) / levels
    out[idx] = kde(np.vstack([a[idx], b[idx]])) < lowest_level
    return out

ws_arr = wind_speed50_clean.to_numpy()
t_arr = temperature50_clean.to_numpy()
ti_arr = turbi50_clean.to_numpy()
month_arr = time.dt.month.to_numpy()

out_ws_t = np.zeros(len(time), dtype=bool)   # wind speed vs temperature outliers
out_ti_ws = np.zeros(len(time), dtype=bool)  # turbulence intensity vs wind speed outliers
for month in range(2, 11):
    for regime_mask in REGIMES.values():
        base = (month_arr == month) & regime_mask
        out_ws_t |= kde_outliers(ws_arr, t_arr, base)
        out_ti_ws |= kde_outliers(ws_arr, ti_arr, base)
out_both = out_ws_t & out_ti_ws

#Month to month time lines: wind speed '--', temperature '-', turbulence intensity '-.'
#night = light grey background, day = white; outlier times highlighted yellow / red / orange (both)
# for month in range(2, 11):
#     m = month_arr == month
#     if not m.any():
#         continue
#     xm = time.values[m]
#     night = ~is_day[m]

#     fig, ax = plt.subplots(figsize=(18, 7))
#     ax_t = ax.twinx()
#     ax_ti = ax.twinx()
#     ax_ti.spines['right'].set_position(('outward', 60))

#     ax.fill_between(xm, 0, 1, where=night, transform=ax.get_xaxis_transform(),
#                     color='lightgrey', alpha=0.6, step='mid', linewidth=0, zorder=0)
#     for flag, color in ((out_ws_t & ~out_both, 'yellow'), (out_ti_ws & ~out_both, 'red'), (out_both, 'orange')):
#         ax.fill_between(xm, 0, 1, where=flag[m], transform=ax.get_xaxis_transform(),
#                         color=color, alpha=0.5, step='mid', linewidth=0, zorder=1)

#     l1, = ax.plot(xm, ws_arr[m], 'b--', lw=0.8, label='Wind Speed @ 50m [m/s]', zorder=3)
#     l2, = ax_t.plot(xm, t_arr[m], 'k-', lw=0.8, label='Temperature @ 50m [deg C]', zorder=3)
#     l3, = ax_ti.plot(xm, ti_arr[m], 'g-.', lw=0.8, label='Turbulence Intensity @ 50m', zorder=3)

#     ax.set_ylabel('Wind Speed [m/s]', color='b')
#     ax_t.set_ylabel('Temperature [deg C]')
#     ax_ti.set_ylabel('Turbulence Intensity', color='g')
#     ax.set_xlim(xm.min(), xm.max())
#     ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))

#     legend_items = [l1, l2, l3,
#                     Patch(facecolor='lightgrey', alpha=0.6, label='Night'),
#                     Patch(facecolor='yellow', alpha=0.5, label='Outlier: wind speed vs temperature'),
#                     Patch(facecolor='red', alpha=0.5, label='Outlier: turbulence intensity vs wind speed'),
#                     Patch(facecolor='orange', alpha=0.5, label='Outlier: both')]
#     ax.legend(handles=legend_items, loc='upper left', ncol=4, fontsize=8)
#     ax.set_title(f'M2 Wind Speed, Temperature and Turbulence Intensity @ 50m - Month {month}')
#     plt.tight_layout()
#     plt.show()
#####################################################################################
# From the plots above we have a visual when the both the outliers occur simultaneously and when they occur individually for each parameter combination
# Print a list and save a cvs of when both the outliers occur simultaneously with the corresponding timestamps and the parameter values
both_outliers_times = time[out_both]
both_outliers_ws = ws_arr[out_both]
both_outliers_t = t_arr[out_both]
both_outliers_ti = ti_arr[out_both]

both_outliers_df = pd.DataFrame({
    'Timestamp': both_outliers_times,
    'Wind Speed @ 50m [m/s]': both_outliers_ws,
    'Temperature @ 50m [deg C]': both_outliers_t,
    'Turbulence Intensity @ 50m': both_outliers_ti
})
print("Both outliers:")
print(both_outliers_df)
both_outliers_df.to_csv('both_outliers.csv', index=False)
