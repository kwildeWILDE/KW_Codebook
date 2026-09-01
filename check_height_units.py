#!/usr/bin/env python
"""Quick script to check height units in TROPoe dataset"""

from TROPoe_Week_Load import load_tropoe_week

# Load just one file's worth of data
ds = load_tropoe_week(['20240818'], verbose=False)

print("Height Coordinate Information:")
print("=" * 60)
print(f"\nHeight values: {ds['height'].values}")
print(f"\nHeight range: {ds['height'].min().values:.2f} to {ds['height'].max().values:.2f}")
print(f"\nHeight data type: {ds['height'].dtype}")
print(f"\nHeight attributes: {ds['height'].attrs}")

print("\n" + "=" * 60)
print("Analysis:")
print("=" * 60)

max_height = ds['height'].max().values
if max_height < 30:
    print(f"✓ Height is in KILOMETERS (max value: {max_height:.2f} km)")
    print("  - Reasonable range for atmospheric data (up to ~17 km altitude)")
else:
    print(f"✓ Height appears to be in METERS (max value: {max_height:.0f} m)")
