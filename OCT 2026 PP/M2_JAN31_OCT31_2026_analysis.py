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
from matplotlib.path import Path
from windrose import WindroseAxes

#############################################
#Pull the Full M2 data from Jan 31 to Oct 17, 2026 

dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_HOUR_JAN31_OCT17_Datapull.xlsx"

#read the file 
#read_excel is slow, so cache it as a pickle and reuse it until the Excel file changes
cache_m2 = file_path_m2.replace('.xlsx', '_cache.pkl')
if os.path.exists(cache_m2) and os.path.getmtime(cache_m2) > os.path.getmtime(file_path_m2):
    ds_m2 = pd.read_pickle(cache_m2)
else:
    ds_m2 = pd.read_excel(file_path_m2)
    ds_m2.to_pickle(cache_m2)

print(ds_m2.head())

#Convert MST into an apporite data format for plotting (HOUR-MST is an integer hour, so add it as a timedelta to the date)
ds_m2['datetime'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str)) + pd.to_timedelta(ds_m2['HOUR-MST'], unit='h')
#the FULL datapull rows are not in time order; sort so time series and flat-run detection are valid
ds_m2 = ds_m2.sort_values('datetime').reset_index(drop=True)
time = ds_m2['datetime']


#from looking over the plot and the excel data there are varibles that have been recorded as "-99999"
#replace these with NaN for proper analysis
ds_m2 = ds_m2.replace(-99999, np.nan)

# ^^^^^ New ds to use that skips the -99999 values

#vairbles for temperature at different heights
temp2 = ds_m2['Avg Temperature @ 2m [deg C]']
temp50 = ds_m2['Avg Temperature @ 50m [deg C]']
temp80 = ds_m2['Avg Temperature @ 80m [deg C]']

#varibles for wind speed at different heights
wind_speed2 = ds_m2['Avg Avg Wind Speed @ 2m [m/s]']
wind_speed5 = ds_m2['Avg Avg Wind Speed @ 5m [m/s]']
wind_speed10 = ds_m2['Avg Avg Wind Speed @ 10m [m/s]']
wind_speed20 = ds_m2['Avg Avg Wind Speed @ 20m [m/s]']
wind_speed50 = ds_m2['Avg Avg Wind Speed @ 50m [m/s]']
wind_speed80 = ds_m2['Avg Avg Wind Speed @ 80m [m/s]']


# # variables for wind direction at different heights
# wind_dir2 = pd.Series(np.nan, index=ds_m2.index)  #hourly datapull has no wind direction columns
# wind_dir5 = pd.Series(np.nan, index=ds_m2.index)  #hourly datapull has no wind direction columns
# wind_dir10 = pd.Series(np.nan, index=ds_m2.index)  #hourly datapull has no wind direction columns
# wind_dir20 = pd.Series(np.nan, index=ds_m2.index)  #hourly datapull has no wind direction columns
# wind_dir50 = pd.Series(np.nan, index=ds_m2.index)  #hourly datapull has no wind direction columns
# wind_dir80 = pd.Series(np.nan, index=ds_m2.index)  #hourly datapull has no wind direction columns

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
# wind_dir50_clean = mask_flat_runs(wind_dir50)  # stuck direction readings (e.g. repeated 0 deg)
# wind_dir80_clean = mask_flat_runs(wind_dir80)
for month in range(2, 11):
    n_flat = (wind_speed10[time.dt.month == month].notna() & wind_speed10_clean[time.dt.month == month].isna()).sum()
    print(f"Month {month}: removed {n_flat} flat wind speed samples")

# create a frequency hitogram with wibull fit line for wind speed at 10 m for the entire period (Feb to Oct 2026)
wind_speed_all = wind_speed10_clean[time.dt.month.isin(range(2, 11))].dropna()
wind_speed_all = wind_speed_all[wind_speed_all > 0]
# plt.figure(figsize=(10, 6))
# plt.hist(wind_speed_all, bins=20, density=True, alpha=0.6, color='b', label='Wind Speed Frequency')
# params = weibull_min.fit(wind_speed_all, floc=0)
# x = np.linspace(0, wind_speed_all.max(), 100)
# plt.plot(x, weibull_min.pdf(x, *params), 'r-', lw=2, label='Weibull Fit')
# plt.title('M2 Wind Speed at 10m - Feb to Oct 2026')
# plt.xlabel('Wind Speed [m/s]')
# plt.ylabel('Frequency')
# plt.legend()
# plt.show()

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
# fig = plt.figure(figsize=(14, 14))
# gs = fig.add_gridspec(3, 3, wspace=0.3, hspace=0.3)
# for i, month in enumerate(range(2, 11)):
#     mask = (time.dt.month == month) & wind_dir80_clean.notna() & wind_speed80_clean.notna()
#     ax = WindroseAxes(fig, gs[i // 3, i % 3].get_position(fig))
#     fig.add_axes(ax)
#     ax.bar(wind_dir80_clean[mask], wind_speed80_clean[mask], normed=True, opening=0.8, edgecolor='white', bins=SPEED_BINS)
#     ax.set_ylim(0, RMAX)
#     ax.set_rgrids(np.linspace(0, RMAX, 5)[1:], labels=[f'{r:.0f}%' for r in np.linspace(0, RMAX, 5)[1:]])
#     ax.set_title(f'Month {month}')
#     if i == 0:
#         ax.set_legend(title='Wind Speed [m/s]', loc='best', bbox_to_anchor=(-0.3, 1.0))
# fig.suptitle('M2 Wind Rose at 80m - Monthly (Feb-Oct 2026, common scale)')
# plt.tight_layout()
# plt.show()

#######################################
ri_250 = ds_m2['Avg Richardson Number (2-50m)']
# ri_280 = ds_m2['Avg Richardson Number (2-80m)']
# ri_5080 = ds_m2['Avg Richardson Number (50-80m)']

ri_250_neg = ri_250[ri_250 < 0]
ri_250_pos = ri_250[ri_250 > 0]


##########################################
# Finding Relevent Events from finding extreme events

#Start creating Bi-vibrate KDE joint plots with raw scatter between wind speed and temperature 
# at JUST 50 m 

#get the clean varaibles first
wind_speed50_clean = mask_flat_runs(wind_speed50)
temperature50_clean = mask_flat_runs(temp50)

#Day/night regimes from solar elevation (NOAA approximation) at the M2 site, using MST (UTC-7, no DST).
#Daytime = sun center above -0.833 deg (standard sunrise/sunset definition, includes refraction).
# M2_LAT, M2_LON, MST_OFFSET_HR = 39.91, -105.23, -7

# def is_daytime(t, lat=M2_LAT, lon=M2_LON, tz=MST_OFFSET_HR):
#     hour = t.dt.hour + t.dt.minute / 60 + t.dt.second / 3600
#     g = 2 * np.pi / 365 * (t.dt.dayofyear - 1 + (hour - 12) / 24)
#     eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
#                        - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
#     decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
#             + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
#     tst = hour * 60 + eqtime + 4 * lon - 60 * tz
#     ha = np.radians(tst / 4 - 180)
#     lat_r = np.radians(lat)
#     sin_elev = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(ha)
#     return (np.degrees(np.arcsin(sin_elev)) > -0.833).to_numpy()

# is_day = is_daytime(time)
# REGIMES = {'Daytime': is_day, 'Nighttime': ~is_day}

#Stability regimes from the 2-50m bulk Richardson number (variable ri_250 above):
#Ri < 0 is unstable (convective), Ri > 0 is stable. Ri == 0 or NaN falls in neither regime.
REGIMES = {'Ri (2-50m) < 0 (unstable)': (ri_250 < 0).to_numpy(),
           'Ri (2-50m) > 0 (stable)': (ri_250 > 0).to_numpy()}
#bivariate KDE joint PDF with raw scatter between 50m wind speed and temperature for the whole period (Jan 31 - Oct 17), split by Ri sign
if True:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharex=True, sharey=True)
    for ax, (regime, regime_mask) in zip(axes, REGIMES.items()):
        mask = regime_mask
        wind_sp = wind_speed50_clean[mask].to_numpy()
        temp = temperature50_clean[mask].to_numpy()
        regime_indices = np.where(mask)[0]  # Get indices for this regime
        valid = ~(np.isnan(wind_sp) | np.isnan(temp))
        wind_sp, temp = wind_sp[valid], temp[valid]
        valid_indices = regime_indices[valid]  # Get the actual indices of valid points
        ax.set_xlabel('Wind Speed @ 50m [m/s]')
        ax.set_ylabel('Temperature @ 50m [deg C]')
        ax.grid(True, linestyle='--', alpha=0.5)
        if wind_sp.size < 3:
            ax.set_title(f'{regime} - insufficient data (n={wind_sp.size})')
            continue

        kde = gaussian_kde(np.vstack([wind_sp, temp]))
        x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
        y = np.linspace(temp.min(), temp.max(), 100)
        X, Y = np.meshgrid(x, y)
        Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

        cf = ax.contourf(X, Y, kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape), levels=15, cmap='viridis', alpha=0.7)
        contours = ax.contour(X, Y, kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape), levels=15, colors='w', linewidths=0.6, zorder=3)
        
        # Get the outer contour paths (outermost level = lowest density level)
        # Use allsegs to get contour line segments for the lowest level (index 0)
        outer_paths = []
        if len(contours.allsegs) > 0:
            # The last index in allsegs corresponds to the outermost/lowest density contour
            outer_segs = contours.allsegs[-1] if len(contours.allsegs) > 0 else []
            if outer_segs:
                # Convert segment arrays to matplotlib Path objects
                for seg in outer_segs:
                    if len(seg) > 2:  # Need at least 3 points to form a closed path
                        # Create a closed path
                        verts = np.vstack([seg, seg[0]])  # Close the path
                        codes = [Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) + [Path.CLOSEPOLY]
                        outer_paths.append(Path(verts, codes))
        
        # Identify points outside outer contour by evaluating KDE at each point
        date_outlier_mask = np.zeros(len(valid_indices), dtype=bool)
        
        # Evaluate KDE density at each point to identify those outside (low density)
        if len(wind_sp) > 0:
            point_densities = kde(np.vstack([wind_sp, temp]))
            
            # Find points with density below outer contour level
            # Use the bottom ~10% as threshold which aligns with the outer contour boundary
            density_threshold = np.percentile(point_densities, 10)  # Bottom 10% are outside the contour
            
            # Check each point
            target_dates_list = [pd.Timestamp('2026-05-07').date(), pd.Timestamp('2026-04-23').date()]
            
            for point_idx, (ws, t, valid_idx) in enumerate(zip(wind_sp, temp, valid_indices)):
                point_density = point_densities[point_idx]
                point_date = time.iloc[valid_idx].date()
                
                # Check if point is outside contour (low density) AND from target date
                if point_density < density_threshold and point_date in target_dates_list:
                    date_outlier_mask[point_idx] = True
        
        # Plot all points in green
        ax.scatter(wind_sp, temp, s=5, c='g', edgecolor='k', linewidth=0.3, alpha=0.7, zorder=2)
        
        # Highlight date-specific outliers in red
        if np.any(date_outlier_mask):
            ax.scatter(wind_sp[date_outlier_mask], temp[date_outlier_mask], 
                      s=150, c='red', marker='*', edgecolor='darkred', linewidth=1.5, 
                      alpha=0.9, zorder=4, label=f'Points outside contour (May 7 & Apr 23)')
            ax.legend(loc='best', fontsize=9)

    fig.suptitle('M2 Wind Speed vs Temperature Bivariate KDE Joint PDF @ 50m - Jan 31 to Oct 17, 2026\n(Red stars: Points outside outer contour on May 7 & Apr 23, 2026)')
    plt.tight_layout()
    plt.show()
############################################################################

#do the same Bi-vibrate KDE joint month by month plots between 50m turbulence intensity and wind speed 
turbi50 = ds_m2['Avg Turbulence Intensity @ 50m']
turbi50_clean = turbi50.where(turbi50.notnull(), np.nan)

if True:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharex=True, sharey=True)
    for ax, (regime, regime_mask) in zip(axes, REGIMES.items()):
        mask = regime_mask
        wind_sp = wind_speed50_clean[mask].to_numpy()
        turbi = turbi50_clean[mask].to_numpy()
        regime_indices = np.where(mask)[0]  # Get indices for this regime
        valid = ~(np.isnan(wind_sp) | np.isnan(turbi))
        wind_sp, turbi = wind_sp[valid], turbi[valid]
        valid_indices = regime_indices[valid]  # Get the actual indices of valid points
        ax.set_xlabel('Wind Speed @ 50m [m/s]')
        ax.set_ylabel('Turbulence Intensity @ 50m')
        ax.grid(True, linestyle='--', alpha=0.5)
        if wind_sp.size < 3:
            ax.set_title(f'{regime} - insufficient data (n={wind_sp.size})')
            continue

        kde = gaussian_kde(np.vstack([wind_sp, turbi]))
        x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
        y = np.linspace(turbi.min(), turbi.max(), 100)
        X, Y = np.meshgrid(x, y)
        Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)
        cf = ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
        contours = ax.contour(X, Y, Z, levels=15, colors='w', linewidths=0.6, zorder=3)
        
        # Identify points outside outer contour by evaluating KDE at each point
        date_outlier_mask = np.zeros(len(valid_indices), dtype=bool)
        
        # Evaluate KDE density at each point to identify those outside (low density)
        if len(wind_sp) > 0:
            point_densities = kde(np.vstack([wind_sp, turbi]))
            
            # Find points with density in the lowest percentile (outside the outer contour)
            density_threshold = np.percentile(point_densities, 10)  # Bottom 10% are likely outside
            
            # Check each point
            target_dates_list = [pd.Timestamp('2026-05-07').date(), pd.Timestamp('2026-04-23').date()]
            
            for point_idx, (ws, t, valid_idx) in enumerate(zip(wind_sp, turbi, valid_indices)):
                point_density = point_densities[point_idx]
                point_date = time.iloc[valid_idx].date()
                
                # Check if point is outside contour (low density) AND from target date
                if point_density < density_threshold and point_date in target_dates_list:
                    date_outlier_mask[point_idx] = True
        
        # Plot all points in green
        ax.scatter(wind_sp, turbi, s=5, c='g', edgecolor='k', linewidth=0.3, alpha=0.7, zorder=2)
        
        # Highlight date-specific outliers in red
        if np.any(date_outlier_mask):
            ax.scatter(wind_sp[date_outlier_mask], turbi[date_outlier_mask], 
                      s=150, c='red', marker='*', edgecolor='darkred', linewidth=1.5, 
                      alpha=0.9, zorder=4, label=f'Points outside contour (May 7 & Apr 23)')
            ax.legend(loc='best', fontsize=9)

    fig.suptitle('M2 Bivariate KDE Joint PDF @ 50m - Jan 31 to Oct 17, 2026 (Turbulence Intensity vs Wind Speed)\n(Red stars: Points outside outer contour on May 7 & Apr 23, 2026)')
    plt.tight_layout()
    plt.show()
#############################################
##
# Now that we have bi-variate KDE plots for turbulence intensity vs wind speed and wind speed vs temperature,
#  we can proceed with further analysis or comparisons as needed.

#both of thses KDE analysis have points that are outside the outer KDE contour ditribution level, 
# indicating potential outliers or extreme values that are not well captured by the KDE.
# Create a whole-period time line of the values of wind speed ('--'), temperature ('-'), and turbulence intensity ('-.') 
# as separate subplots on a shared time axis (grey shading where the 2-50 m Ri is negative)

# For the outliers points from the pervious KDE, plot a highlierted line of WHEN the outliers occur over time.
#For the outlier ofwind speed and temperature highlight with the color yellow in time 
#for the outlier of turbulence intensity and wind speed highlight with the color red in time 
#that so we can see when oulieres for both tpes of bi-variate KDE appear as the color orange (color mixing)

#Outliers = samples outside the outermost KDE contour (density below the lowest contour level),
#computed over the whole period for each Ri regime, exactly like the KDE plots above.
#Also returns the KDE joint PDF density at every sample (NaN where not evaluated); the outliers are the
#samples whose density is below the lowest contour level.
# def kde_outliers(a, b, base_mask, levels=15):
#     out = np.zeros(len(a), dtype=bool)
#     dens = np.full(len(a), np.nan)
#     a, b = np.asarray(a), np.asarray(b)
#     idx = np.where(base_mask & ~(np.isnan(a) | np.isnan(b)))[0]
#     if idx.size < 3:
#         return out, dens
#     kde = gaussian_kde(np.vstack([a[idx], b[idx]]))
#     x = np.linspace(a[idx].min(), a[idx].max(), 100)
#     y = np.linspace(b[idx].min(), b[idx].max(), 100)
#     X, Y = np.meshgrid(x, y)
#     Z = kde(np.vstack([X.ravel(), Y.ravel()]))
#     lowest_level = Z.min() + (Z.max() - Z.min()) / levels
#     dens[idx] = kde(np.vstack([a[idx], b[idx]]))
#     out[idx] = dens[idx] < lowest_level
#     return out, dens

def kde_outliers(a, b, base_mask, levels=15):
    out = np.zeros(len(a), dtype=bool)
    dens = np.full(len(a), np.nan)
    a, b = np.asarray(a), np.asarray(b)
    idx = np.where(base_mask & ~(np.isnan(a) | np.isnan(b)))[0]
    if idx.size < 3:
        return out, dens
    kde = gaussian_kde(np.vstack([a[idx], b[idx]]))
    x = np.linspace(a[idx].min(), a[idx].max(), 100)
    y = np.linspace(b[idx].min(), b[idx].max(), 100)
    X, Y = np.meshgrid(x, y)
    Z = kde(np.vstack([X.ravel(), Y.ravel()]))
    lowest_level = Z.min() + (Z.max() - Z.min()) / levels
    dens[idx] = kde(np.vstack([a[idx], b[idx]]))
    out[idx] = dens[idx] < lowest_level
    return out, dens

ws_arr = wind_speed50_clean.to_numpy()
t_arr = temperature50_clean.to_numpy()
ti_arr = turbi50_clean.to_numpy()
out_ws_t = np.zeros(len(time), dtype=bool)   # wind speed vs temperature outliers
out_ti_ws = np.zeros(len(time), dtype=bool)  # turbulence intensity vs wind speed outliers
dens_ws_t = np.full(len(time), np.nan)       # joint PDF density, wind speed vs temperature
dens_ti_ws = np.full(len(time), np.nan)      # joint PDF density, turbulence intensity vs wind speed
#whole period (Jan 31 - Oct 17), one KDE per Ri regime, matching the KDE plots above
for regime_mask in REGIMES.values():
    o, d = kde_outliers(ws_arr, t_arr, regime_mask)
    out_ws_t |= o; dens_ws_t[~np.isnan(d)] = d[~np.isnan(d)]
    o, d = kde_outliers(ws_arr, ti_arr, regime_mask)
    out_ti_ws |= o; dens_ti_ws[~np.isnan(d)] = d[~np.isnan(d)]
out_both = out_ws_t & out_ti_ws

# # Whole-period time line (Jan 31 - Oct 17) with a separate subplot per variable on a shared time axis.
# # Grey shading = 2-50 m Ri < 0 (unstable); outlier times highlighted yellow / red / orange (both)
# xt = time.values
# unstable = REGIMES['Ri (2-50m) < 0 (unstable)']
# series = [(ws_arr, 'Wind Speed @ 50m [m/s]', 'b', '-'),
#           (t_arr, 'Temperature @ 50m [deg C]', 'k', '-'),
#           (ti_arr, 'Turbulence Intensity @ 50m', 'g', '-')]

# fig, axes = plt.subplots(len(series), 1, figsize=(18, 10), sharex=True)
# for ax, (values, label, color, ls) in zip(axes, series):
#     ax.fill_between(xt, 0, 1, where=unstable, transform=ax.get_xaxis_transform(),
#                     color='grey', alpha=0.35, step='mid', linewidth=0, zorder=0)
#     for flag, c in ((out_ws_t & ~out_both, 'yellow'), (out_ti_ws & ~out_both, 'red'), (out_both, 'orange')):
#         ax.fill_between(xt, 0, 1, where=flag, transform=ax.get_xaxis_transform(),
#                         color=c, alpha=0.5, step='mid', linewidth=0, zorder=1)
#     ax.plot(xt, values, color=color, ls=ls, lw=0.8, zorder=3)
#     ax.set_ylabel(label)
#     ax.grid(True, linestyle='--', alpha=0.3)
# axes[0].legend(handles=[Patch(facecolor='grey', alpha=0.35, label='Ri (2-50m) < 0'),
#                         Patch(facecolor='yellow', alpha=0.5, label='Outlier: wind speed vs temperature'),
#                         Patch(facecolor='red', alpha=0.5, label='Outlier: turbulence intensity vs wind speed'),
#                         Patch(facecolor='orange', alpha=0.5, label='Outlier: both')],
#                loc='upper left', ncol=4, fontsize=8)
# axes[-1].set_xlim(xt.min(), xt.max())
# axes[-1].xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
# axes[-1].set_xlabel('Time (MST)')
# fig.suptitle('M2 Wind Speed, Temperature and Turbulence Intensity @ 50m - Jan 31 to Oct 17, 2026')
# plt.tight_layout()
# plt.show()

#####################################################################################
# From the plots above we have a visual when the both the outliers occur simultaneously and when they occur individually for each parameter combination
# Print a list and save a cvs of when both the outliers occur simultaneously with the corresponding timestamps and the parameter values
both_outliers_times = time[out_both]
both_outliers_ws = ws_arr[out_both]
both_outliers_t = t_arr[out_both]
both_outliers_ti = ti_arr[out_both]
#KDE joint PDF density of each outlier in its two bivariate KDEs (units: 1 / (unit_a * unit_b)); low = rarer.
#The percentile is the share of all valid samples of that KDE with a density at or below this point's.
def density_percentile(dens):
    valid = dens[~np.isnan(dens)]
    return np.array([(valid <= d).mean() * 100 for d in dens[out_both]])

both_outliers_df = pd.DataFrame({
    'Timestamp': both_outliers_times,
    'Wind Speed @ 50m [m/s]': both_outliers_ws,
    'Temperature @ 50m [deg C]': both_outliers_t,
    'Turbulence Intensity @ 50m': both_outliers_ti,
    'Joint PDF density (wind speed, temperature)': dens_ws_t[out_both],
    'Joint PDF density (turbulence intensity, wind speed)': dens_ti_ws[out_both],
    'Density percentile (wind speed, temperature) [%]': density_percentile(dens_ws_t),
    'Density percentile (turbulence intensity, wind speed) [%]': density_percentile(dens_ti_ws),
    'Ri (2-50m)': ri_250.to_numpy()[out_both]
})
print("Both outliers:")
print(both_outliers_df)
both_outliers_df.to_csv('M2_HOUR_50mboth_outliers.csv', index=False)

########################################### 
#Now that we have a method to filter out when both of the outliers happen at the same time, 
# we can can see the frequency of when both outliers occur simultaneously
#an exmple is to create a month to month frquency histogtram with a weibull fit of when the outliers occur simultaneously
#over time of the day (0 - 23 hours)
#for the 
# both_outliers_times = pd.Series(pd.to_datetime(both_outliers_times.to_numpy()))
# for month in range(1, 13):
#     both_outliers_month = both_outliers_times[both_outliers_times.dt.month == month]
#     if both_outliers_month.empty:
#         continue
#     both_outliers_hours = both_outliers_month.dt.hour.to_numpy()
#     plt.figure(figsize=(10, 6))
#     plt.hist(both_outliers_hours, bins=np.arange(0, 25) - 0.5, edgecolor='black', alpha=0.7,
#              label=f'Observed, (n={len(both_outliers_hours)})')
#     #Weibull fit (location fixed at 0); shift by 0.5 so hour 0 is valid, scale pdf to counts
#     if len(np.unique(both_outliers_hours)) > 1:
#         shape, loc, scale = weibull_min.fit(both_outliers_hours + 0.5, floc=0)
#         xs = np.linspace(0, 24, 200)
#         plt.plot(xs, weibull_min.pdf(xs + 0.5, shape, loc, scale) * len(both_outliers_hours),
#                  'r-', lw=2, label=f'Weibull fit (k={shape:.2f}, c={scale:.2f})')
#     plt.legend()
#     plt.xlabel('Hour of the Day')
#     plt.ylabel('Frequency of Both Outliers')
#     plt.title(f'M2 Frequency of Both Outliers @ 50m Occurring Simultaneously by Hour of the Day for month {month}', fontsize=8)
#     plt.xticks(range(0, 24))
#     plt.show()
