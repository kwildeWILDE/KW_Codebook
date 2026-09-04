#Import Libraries
import numpy as np
import pandas as pd
import xarray as xr 
import matplotlib.pyplot as plt
import os 
from pathlib import Path

# Import the TROPoe loader function
from TROPoe_Week_Load import load_tropoe_week

# ============================================================================
# LOAD TROPOE DATA
# ============================================================================
# Specify which dates to load (format: YYYYMMDD)
# Note: Available data is Aug 18 - Sep 17, 2024

# Option 1: Load first week (Aug 18-25, 2024)
target_dates = ['20240818', '20240819', '20240820', '20240821', 
                '20240822', '20240823', '20240824', '20240825']


print("Loading TROPoe dataset...")
ds = load_tropoe_week(target_dates, verbose=True)

print("\n" + "=" * 70)
print("HEIGHT INDEX REFERENCE")
print("=" * 70)

heights_km = ds['height'].values  # Height values in km

# Create a DataFrame for easy viewing
height_index_df = pd.DataFrame({
    'Index': range(len(heights_km)),
    'Height (km)': heights_km
})

print(height_index_df.to_string(index=False))


#creating a plot of water vapor at a specific height across the week

# Extract and plot water vapor data at the different levels of the troposphere 
wv_at_height_l = ds['waterVapor'].isel(height=27).values # (height index 27 = ~1.21 km)

wv_at_height_m = ds['waterVapor'].isel(height=47).values # (height index 47 = ~8.72 km)

wv_at_height_u = ds['waterVapor'].isel(height=54).values # (height index 54 = ~17.09 km)

#extracting and plotting the qc_flags over the time period for the different levels of the troposphere
qc_ind_overall = ds['qc_flag']

times = ds['time'].values

y1 = ds['waterVapor']
y2 = ds['qc_flag']

fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.plot(times, wv_at_height_l, linewidth=2,color='blue', label='Lower Troposphere ~1.21 km')

ax1.plot(times, wv_at_height_m, linewidth=2, color='green', label='Middle Troposphere ~8.72 km')

ax1.plot(times, wv_at_height_u, linewidth=2, color='red', label='Upper Troposphere ~17.09 km')

ax1.set_xlabel('Time', fontsize=12)
ax1.set_ylabel('Water Vapor (g/kg)', fontsize=12)
ax1.legend(loc='upper right', fontsize=10)

ax2 = ax1.twinx()  # Create a second y-axis for QC flags
ax2.plot(times, qc_ind_overall, linewidth=1, color='orange', label='QC Flag', alpha=0.5)
ax2.set_ylabel('QC Flag', fontsize=12)

ax2.legend(loc='upper left', fontsize=10)
plt.title('Water Vapor Profile at Different Tropospheric Levels', fontsize=14)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

plt.tight_layout()

output_path = 'output_plots/TROPoe_AUG1825_2024_plots/TROPoe_water_vapor_plot.png'
os.makedirs('output_plots', exist_ok=True)
plt.savefig(output_path, dpi=150)
print(f"\n✓ Plot saved to: {output_path}")

plt.show()  # Show the plot in an interactive window