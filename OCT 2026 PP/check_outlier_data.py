#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic script to check if there are data points on May 7 and April 23, 2026
and if any are outside the KDE contours
"""
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

# Load data
dp_m2 = "C:/Users/kwilde/OneDrive - NLR/Documents"
file_path_m2 = f"{dp_m2}/M2_HOUR_JAN31_OCT17_Datapull.xlsx"

print("Loading data...")
ds_m2 = pd.read_excel(file_path_m2)
ds_m2 = ds_m2.replace(-99999, np.nan)

# Convert datetime
ds_m2['datetime'] = pd.to_datetime(ds_m2['DATE (MM/DD/YYYY)'].astype(str)) + pd.to_timedelta(ds_m2['HOUR-MST'], unit='h')
ds_m2 = ds_m2.sort_values('datetime').reset_index(drop=True)
time = ds_m2['datetime']

# Get variables
temp50 = ds_m2['Avg Temperature @ 50m [deg C]']
wind_speed50 = ds_m2['Avg Avg Wind Speed @ 50m [m/s]']
turbi50 = ds_m2['Avg Turbulence Intensity @ 50m']
ri_250 = ds_m2['Avg Richardson Number (2-50m)']

# Check for data on target dates
target_dates = [pd.Timestamp('2026-05-07').date(), pd.Timestamp('2026-04-23').date()]

print("\n" + "="*80)
print("CHECKING DATA ON TARGET DATES")
print("="*80)

for target_date in target_dates:
    print(f"\nDate: {target_date}")
    mask = time.dt.date == target_date
    count = mask.sum()
    print(f"   Total data points: {count}")
    
    if count > 0:
        # Get unstable points (Ri < 0)
        unstable_mask = mask & (ri_250 < 0)
        print(f"   - Unstable points (Ri < 0): {unstable_mask.sum()}")
        
        # Get stable points (Ri > 0)
        stable_mask = mask & (ri_250 > 0)
        print(f"   - Stable points (Ri > 0): {stable_mask.sum()}")

print("\n" + "="*80)
print("CHECKING FOR POINTS OUTSIDE KDE CONTOURS")
print("="*80)

REGIMES = {'Ri (2-50m) < 0 (unstable)': (ri_250 < 0).to_numpy(),
           'Ri (2-50m) > 0 (stable)': (ri_250 > 0).to_numpy()}

# Temperature vs Wind Speed
print("\nWIND SPEED vs TEMPERATURE @ 50m")
print("-" * 80)

for regime_name, regime_mask in REGIMES.items():
    wind_sp = wind_speed50[regime_mask].dropna().values
    temp = temp50[regime_mask].dropna().values
    valid = ~(np.isnan(wind_sp) | np.isnan(temp))
    wind_sp = wind_sp[valid]
    temp = temp[valid]
    
    if len(wind_sp) < 3:
        continue
    
    # Compute KDE
    kde = gaussian_kde(np.vstack([wind_sp, temp]))
    point_densities = kde(np.vstack([wind_sp, temp]))
    density_threshold = np.percentile(point_densities, 5)
    
    print(f"\n{regime_name}")
    print(f"  Total points: {len(wind_sp)}")
    print(f"  Density threshold (5th percentile): {density_threshold:.6f}")
    
    # Check on target dates
    for target_date in target_dates:
        date_mask_regime = regime_mask & (time.dt.date == target_date)
        if date_mask_regime.sum() > 0:
            indices = np.where(date_mask_regime)[0]
            ws_date = wind_speed50.iloc[indices].dropna().values
            temp_date = temp50.iloc[indices].dropna().values
            
            # Get densities for these points
            if len(ws_date) > 0 and len(temp_date) > 0:
                densities_date = kde(np.vstack([ws_date, temp_date]))
                outside_count = (densities_date < density_threshold).sum()
                print(f"  {target_date}: {len(ws_date)} points, {outside_count} outside contour")

# Turbulence Intensity vs Wind Speed
print("\n\nWIND SPEED vs TURBULENCE INTENSITY @ 50m")
print("-" * 80)

for regime_name, regime_mask in REGIMES.items():
    wind_sp = wind_speed50[regime_mask].dropna().values
    turbi = turbi50[regime_mask].dropna().values
    valid = ~(np.isnan(wind_sp) | np.isnan(turbi))
    wind_sp = wind_sp[valid]
    turbi = turbi[valid]
    
    if len(wind_sp) < 3:
        continue
    
    # Compute KDE
    kde = gaussian_kde(np.vstack([wind_sp, turbi]))
    point_densities = kde(np.vstack([wind_sp, turbi]))
    density_threshold = np.percentile(point_densities, 5)
    
    print(f"\n{regime_name}")
    print(f"  Total points: {len(wind_sp)}")
    print(f"  Density threshold (5th percentile): {density_threshold:.6f}")
    
    # Check on target dates
    for target_date in target_dates:
        date_mask_regime = regime_mask & (time.dt.date == target_date)
        if date_mask_regime.sum() > 0:
            indices = np.where(date_mask_regime)[0]
            ws_date = wind_speed50.iloc[indices].dropna().values
            turbi_date = turbi50.iloc[indices].dropna().values
            
            # Get densities for these points
            if len(ws_date) > 0 and len(turbi_date) > 0:
                densities_date = kde(np.vstack([ws_date, turbi_date]))
                outside_count = (densities_date < density_threshold).sum()
                print(f"  {target_date}: {len(ws_date)} points, {outside_count} outside contour")

print("\n" + "="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80 + "\n")
