#importing libaries
import numpy as np
import xarray as xr
from pathlib import Path
import matplotlib.pyplot as plt

#getting the s40 lidar data from the CORSAIR fc.s40lidar.z01.c1
data_dir = Path("C:/Users/kwilde/Documents/GitHub/KW_Codebook/WDH_Data/corsair/s40.lidar.z01.b0/order_7a42b196507540cab667c1688")

#creating the xarray data from the nc files from the lidar order 
nc_files = sorted(data_dir.glob("*.nc"))
if not nc_files:
    raise FileNotFoundError(f"No NetCDF files found in {data_dir}")

# Debug: inspect the structure of the first file before concatenating
sample_ds = xr.open_dataset(nc_files[0])
print("Sample file dims:", dict(sample_ds.sizes))
print("Sample file coords:", list(sample_ds.coords))
print("Time coordinate:", sample_ds["time"])

# time is a 2D data variable (beamID, scanID), not an actual dimension.
# Each file represents a separate block of scans, so concatenate along 'scanID'
# and give each file's scanID values a unique, monotonically increasing offset
# so scans from different files don't collide/overlap.
datasets = []
scan_offset = 0
for filepath in nc_files:
    file_ds = xr.open_dataset(filepath)
    n_scans = file_ds.sizes["scanID"]
    file_ds = file_ds.assign_coords(scanID=np.arange(scan_offset, scan_offset + n_scans))
    scan_offset += n_scans
    datasets.append(file_ds)

ds = xr.concat(
    datasets,
    dim="scanID",
    data_vars="all",
    coords="minimal",
    compat="override",
    combine_attrs="override",
    join="outer",
)

# Sort scans chronologically using the mean time across beams for each scan
# (time should be effectively the same across beams within a scan, but taking
# the mean guards against any tiny per-beam timing differences).
mean_scan_time = ds["time"].mean(dim="beamID")
sort_order = np.argsort(mean_scan_time.values)
ds = ds.isel(scanID=sort_order)

# See the variables and dimensions in the combined dataset.
print("Files loaded:", len(nc_files))
print("Variables:", list(ds.data_vars))
print("Dimensions:", dict(ds.sizes))
print("Time range:", ds["time"].values.min(), "to", ds["time"].values.max())

print(ds)