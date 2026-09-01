"""
TROPoe Data Loader Module

Load TROPoe .nc files with automatic handling of dimension conflicts.
This module provides a reusable function to load subsets of TROPoe data.

Key features:
- Uses join='override' to handle obs_dim conflicts
- Lazy loading with dask (memory efficient)
- Easily configurable date ranges
"""

import xarray as xr
import os
import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

# Default data directory
DEFAULT_DATA_DIR = "C:/Users/kwilde/Documents/GitHub/KW_Codebook/TROPoe_Data_Pull/order_1757a1568ad84dfda0f15b602"


def load_tropoe_week(target_dates, data_dir=DEFAULT_DATA_DIR, verbose=True):
    """
    Load TROPoe data for specified dates.
    
    Parameters:
    -----------
    target_dates : list of str
        List of date strings in format 'YYYYMMDD' (e.g., ['20240818', '20240819'])
    data_dir : str
        Path to directory containing .nc files
    verbose : bool
        If True, print loading progress and dataset info
    
    Returns:
    --------
    ds : xarray.Dataset
        Combined dataset with lazy loading (dask arrays)
    
    Example:
    --------
    >>> target_dates = ['20240818', '20240819', '20240820']
    >>> ds = load_tropoe_week(target_dates)
    >>> temp = ds['temperature'].compute()  # Load into memory
    """
    
    # Get all available files
    all_files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                       if f.endswith('.nc')])
    
    if verbose:
        print(f"Total files available: {len(all_files)}")
        print(f"Date range: Aug 18 - Sep 17, 2024\n")
    
    # Filter for specified dates
    week_files = [f for f in all_files if any(date in f for date in target_dates)]
    
    if verbose:
        print(f"Files selected ({len(week_files)} total):")
        for f in week_files:
            print(f"  - {os.path.basename(f)}")
        print()
    
    if not week_files:
        raise FileNotFoundError(f"No files found for dates: {target_dates}")
    
    # Load files
    if verbose:
        print("=" * 70)
        print(f"LOADING {len(week_files)} FILES")
        print("=" * 70)
        print("Loading files individually...")
    
    datasets = []
    for i, filepath in enumerate(week_files):
        filename = os.path.basename(filepath)
        if verbose:
            print(f"  [{i+1:2d}/{len(week_files)}] {filename}", end='\r')
        
        # Open with lazy loading
        ds = xr.open_dataset(filepath, chunks='auto')
        datasets.append(ds)
    
    if verbose:
        print(f"\n✓ Successfully loaded {len(datasets)} files\n")
        print("Concatenating along time dimension...")
        print("(Using join='override' to handle obs_dim size conflicts)\n")
    
    # KEY FIX: Use join='override' to handle dimension conflicts
    ds_combined = xr.concat(
        datasets,
        dim='time',
        join='override',  # ← Ignores dimension mismatches in non-concat dims
        coords='minimal'
    )
    
    if verbose:
        print("✓ Successfully combined all data!\n")
        print("=" * 70)
        print("DATASET INFO")
        print("=" * 70)
        print(ds_combined)
        print(f"\nDimensions: {dict(ds_combined.dims)}")
        print(f"Time range: {ds_combined.time.values[0]} to {ds_combined.time.values[-1]}")
        print(f"Variables: {len(ds_combined.data_vars)}")
        print(f"Total size: {ds_combined.nbytes / 1e9:.2f} GB (when computed)")
        print("=" * 70)
    
    return ds_combined


if __name__ == "__main__":
    # Example usage when run directly
    print("TROPoe Week Loader\n")
    
    # Load Aug 18-25, 2024 (first week)
    target_dates = ['20240818', '20240819', '20240820', '20240821', 
                    '20240822', '20240823', '20240824', '20240825']
    
    try:
        ds_week = load_tropoe_week(target_dates)
        
        print("\n" + "=" * 70)
        print("QUICK START - ACCESS YOUR DATA:")
        print("=" * 70)
        print("\n1. View variables:")
        print("   print(list(ds_week.data_vars))")
        print("\n2. Access a variable (lazy):")
        print("   temp = ds_week['temperature']  # Still lazy, not in memory")
        print("\n3. Load into memory:")
        print("   temp_data = ds_week['temperature'].compute()")
        print("\n4. Plot temperature at specific height:")
        print("   ds_week['temperature'].isel(height=27).plot()  # height=27 is ~8.5km")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}")
        print(f"   {e}")
        
        print("\n" + "=" * 70)
        print("KEY INFO:")
        print("=" * 70)
        print(f"Dimensions: {dict(ds_week.dims)}")
        print(f"Time range: {ds_week.time.values[0]} to {ds_week.time.values[-1]}")
        print(f"Variables available: {len(ds_week.data_vars)}")
        print(f"\nTotal size: {ds_week.nbytes / 1e9:.2f} GB (when fully computed)")
        
        print("\n" + "=" * 70)
        print("QUICK START - ACCESS YOUR DATA:")
        print("=" * 70)
        print("\n1. View variables:")
        print("   print(list(ds_week.data_vars))")
        
        print("\n2. Access a variable (lazy):")
        print("   temp = ds_week['temperature']  # Still lazy, not in memory")
        
        print("\n3. Load into memory:")
        print("   temp_data = ds_week['temperature'].compute()")
        
        print("\n4. Get mean temperature:")
        print("   mean_temp = ds_week['temperature'].mean().compute()")
        
        print("\n5. Plot temperature at specific height:")
        print("   ds_week['temperature'].isel(height=27).plot()  # height=27 is ~8.5km")
        
        print("\n6. Save to new NetCDF file:")
        print("   ds_week.to_netcdf('tropoe_week_aug7-18.nc')")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}")
        print(f"   {e}")
        print("\nThis error means there's still a dimension conflict.")
        print("Possible solutions:")
        print("  1. Load individual files separately")
        print("  2. Use only specific variables (not entire dataset)")
        print("  3. Try a single file first to test")
